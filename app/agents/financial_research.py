from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.agents.financial_calculations import calculate_profit_margin
from app.agents.models import FinancialResearchResult
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
            "Do not invent financial data.",
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
        FinancialResearchResult
    )
)


financial_research_tool_loop = build_tool_loop_graph(
    FINANCIAL_RESEARCH_TOOLS
)


def extract_tool_results(
    tool_result: dict,
) -> str:

    tool_messages = [
        message
        for message in tool_result["messages"]
        if message.type == "tool"
    ]

    return "\n".join(
        message.content
        for message in tool_messages
    )


def financial_research_agent(
    state: FinancialResearchState,
) -> FinancialResearchState:

    ticker = state["ticker"]

    prompt_value = financial_research_prompt.invoke(
        {
            "ticker": ticker,
        }
    )

    try:
        tool_result = financial_research_tool_loop.invoke(
            {
                "messages": prompt_value.messages,
            }
        )

        research_context = extract_tool_results(
            tool_result
        )

        structured_result = (
            structured_financial_research_llm.invoke(
                [
                    *prompt_value.messages,
                    HumanMessage(
                        content=(
                            "Tool results:\n"
                            f"{research_context}\n\n"
                            "Using only these tool results, "
                            "produce the structured financial "
                            "research result. "
                            "Do not calculate profit margin; "
                            "the application will calculate it "
                            "deterministically."
                        )
                    ),
                ]
            )
        )

        structured_result.profit_margin = calculate_profit_margin(
            structured_result.revenue,
            structured_result.net_income,
        )

    except Exception as exc:
        return {
            "research_result": None,
            "research_error": str(exc),
        }

    return {
        "research_result": structured_result,
        "research_error": "",
    }


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