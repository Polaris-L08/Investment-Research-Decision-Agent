from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.agents.financial_calculations import calculate_profit_margin
from app.agents.models import FinancialResearchResult
from app.agents.research_contracts import require_research_result, research_failure, research_success, \
    is_timeout_failure, mark_research_complete, require_tool_calls_match_ticker, parse_tool_payloads_by_name, \
    require_finite_number
from app.agents.tool_sets import FINANCIAL_RESEARCH_TOOLS
from app.graph.tool_loop import build_tool_loop_graph
from app.llm.client import llm


class FinancialResearchInputState(TypedDict):
    ticker: str


class FinancialResearchState(TypedDict):
    ticker: str
    research_result: FinancialResearchResult | None
    research_error: str


class FinancialResearchOutputState(TypedDict):
    research_result: FinancialResearchResult | None
    research_error: str


financial_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Financial Research Agent. "
            "Your responsibility is to research basic financial "
            "performance for the given stock ticker. "
            "Use the available tools to obtain revenue and "
            "net income. "
            "Return revenue and net income from the available data. "
            "The application will calculate profit margin "
            "deterministically. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent financial data. "
            "The data_status and degradation_reason fields are system-managed; "
            "leave them at their defaults.",
        ),
        (
            "human",
            "Research the financial performance of the following "
            "company and return a concise financial research result.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)


structured_financial_research_llm = (
    llm.with_structured_output(
        FinancialResearchResult,
        method="function_calling"
    )
)


financial_research_tool_loop = build_tool_loop_graph(
    FINANCIAL_RESEARCH_TOOLS
)


def extract_tool_results(
    tool_result: dict,
) -> str:
    """Return tool output text for the narrative prompt only."""
    tool_messages = [
        message
        for message in tool_result["messages"]
        if message.type == "tool"
    ]

    return "\n".join(
        message.content
        for message in tool_messages
    )


def build_financial_research_fallback(
    tool_result: dict, *, ticker: str
) -> FinancialResearchResult:
    """Build a degraded financial result from actual revenue/net-income tool data."""
    required_tools = {"get_revenue", "get_net_income"}

    payloads = parse_tool_payloads_by_name(
        tool_result,
        allowed_names=required_tools
    )
    if not required_tools.issubset(payloads):
        raise ValueError("Fallback requires successful revenue and net-income tool outputs.")

    require_tool_calls_match_ticker(tool_result, ticker, required_tools)

    revenue = require_finite_number(payloads["get_revenue"], "revenue")
    net_income = require_finite_number(payloads["get_net_income"], "net income")

    if revenue <= 0:
        raise ValueError("Fallback requires positive revenue to calculate profit margin.")
    margin = calculate_profit_margin(revenue, net_income)
    return FinancialResearchResult(
        ticker=ticker.strip().upper(),
        revenue=revenue,
        net_income=net_income,
        profit_margin=margin,
        summary=(
            "DEGRADED FALLBACK: Structured LLM synthesis was unavailable. "
            f"Provider outputs returned revenue of {revenue}, net income of "
            f"{net_income}, and a deterministically calculated profit margin of {margin}."
        ),
        data_status="degraded",
        degradation_reason=(
            "Structured LLM synthesis failed; revenue and net income were retained "
            "from successful tool outputs and profit margin was calculated deterministically."
        ),
    )


def financial_research_agent(
    state: FinancialResearchState,
) -> FinancialResearchState:
    ticker = state["ticker"]
    prompt_value = financial_research_prompt.invoke({"ticker": ticker})
    try:
        tool_result = financial_research_tool_loop.invoke(
            {"messages": prompt_value.messages}
        )
    except Exception as exc:
        return research_failure(exc)

    try:
        research_context = extract_tool_results(tool_result)
    except Exception as exc:
        return research_failure(exc)

    try:
        structured_result = structured_financial_research_llm.invoke(
            [
                *prompt_value.messages,
                HumanMessage(
                    content=(
                        "Tool results:\n"
                        f"{research_context}\n\n"
                        "Using only these tool results, produce the structured financial "
                        "research result. Do not calculate profit margin; the application "
                        "will calculate it deterministically."
                    )
                ),
            ]
        )

        structured_result = require_research_result(
            structured_result, FinancialResearchResult
        )

        structured_result.profit_margin = calculate_profit_margin(
            structured_result.revenue, structured_result.net_income
        )
        return research_success(mark_research_complete(structured_result))
    except Exception as synthesis_error:
        if is_timeout_failure(synthesis_error):
            return research_failure(synthesis_error)
        try:
            fallback_result = build_financial_research_fallback(tool_result, ticker=ticker)
        except Exception as fallback_error:
            return research_failure(
                RuntimeError(
                    "Structured financial research failed and evidence-backed fallback "
                    "was unavailable. "
                    f"Synthesis error: {type(synthesis_error).__name__}; "
                    f"fallback error: {fallback_error}"
                )
            )
        return research_success(fallback_result)


def build_financial_research_graph():

    builder = StateGraph(
        FinancialResearchState,
        input_schema=FinancialResearchInputState,
        output_schema=FinancialResearchOutputState,
    )

    builder.add_node(
        "financial_research_agent",
        financial_research_agent,
    )

    builder.add_edge(
        START,
        "financial_research_agent",
    )

    builder.add_edge(
        "financial_research_agent",
        END,
    )

    return builder.compile()


financial_research_graph = (
    build_financial_research_graph()
)