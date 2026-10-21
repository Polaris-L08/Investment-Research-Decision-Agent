from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agents.models import IndustryMacroResearchResult
from app.agents.research_contracts import require_research_result, research_failure, research_success, \
    require_matching_ticker, require_tool_calls_match_ticker, parse_tool_payloads_by_name, require_nonempty_string, \
    require_finite_number, mark_research_complete, is_timeout_failure
from app.agents.tool_sets import INDUSTRY_MACRO_RESEARCH_TOOLS
from app.graph.tool_loop import build_tool_loop_graph
from app.llm.client import llm


class IndustryMacroResearchInputState(TypedDict):
    ticker: str


class IndustryMacroResearchState(TypedDict):
    ticker: str
    research_result: IndustryMacroResearchResult | None
    research_error: str


class IndustryMacroResearchOutputState(TypedDict):
    research_result: IndustryMacroResearchResult | None
    research_error: str


industry_macro_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an Industry and Macro Research Agent. "
            "Your responsibility is to research the basic industry "
            "and macroeconomic environment for the given stock ticker. "
            "Use the available tools to obtain industry information "
            "and macroeconomic environment information. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent industry or macroeconomic data. "
            "The data_status and degradation_reason fields are system-managed; "
            "leave them at their defaults.",
        ),
        (
            "human",
            "Research the industry and macroeconomic environment "
            "for the following company and return a concise "
            "industry and macro research result.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)


industry_macro_research_tool_loop = build_tool_loop_graph(
    INDUSTRY_MACRO_RESEARCH_TOOLS
)


structured_industry_macro_research_llm = llm.with_structured_output(
    IndustryMacroResearchResult,
    method="function_calling"
)


def extract_tool_results(tool_result: dict) -> str:
    tool_messages = [
        message
        for message in tool_result["messages"]
        if message.type == "tool"
    ]

    return "\n".join(message.content for message in tool_messages)


def build_industry_macro_research_fallback(
    tool_result: dict, *, ticker: str
) -> IndustryMacroResearchResult:
    """Build a degraded industry/macro result from both successful data tools."""
    required_tools = {"get_industry_info", "get_macro_environment"}
    require_tool_calls_match_ticker(tool_result, ticker, required_tools)
    payloads = parse_tool_payloads_by_name(tool_result, allowed_names=required_tools)
    industry_payload = payloads.get("get_industry_info")
    macro_payload = payloads.get("get_macro_environment")
    if industry_payload is None or macro_payload is None:
        raise ValueError(
            "Fallback requires successful industry-info and macro-environment tool outputs."
        )
    require_matching_ticker(industry_payload, ticker, "industry-info")
    require_matching_ticker(macro_payload, ticker, "macro-environment")
    industry = require_nonempty_string(industry_payload.get("industry"), "industry")
    industry_growth = require_finite_number(
        industry_payload.get("industry_growth"), "industry growth"
    )
    macro_environment = require_nonempty_string(
        macro_payload.get("macro_environment"), "macro environment"
    )
    macro_growth = require_finite_number(macro_payload.get("macro_growth"), "macro growth")
    return IndustryMacroResearchResult(
        ticker=ticker.strip().upper(),
        industry=industry,
        industry_growth=industry_growth,
        macro_environment=macro_environment,
        macro_growth=macro_growth,
        summary=(
            "DEGRADED FALLBACK: Structured LLM synthesis was unavailable. "
            f"Provider outputs returned industry {industry} with growth {industry_growth}, "
            f"and macro environment {macro_environment} with growth {macro_growth}."
        ),
        data_status="degraded",
        degradation_reason=(
            "Structured LLM synthesis failed; industry and macro fields were retained "
            "from successful tool outputs without adding an interpretation."
        ),
    )


def industry_macro_research_agent(
    state: IndustryMacroResearchState,
) -> IndustryMacroResearchState:
    ticker = state["ticker"]
    prompt_value = industry_macro_research_prompt.invoke({"ticker": ticker})
    try:
        tool_result = industry_macro_research_tool_loop.invoke(
            {"messages": prompt_value.messages}
        )
    except Exception as exc:
        return research_failure(exc)

    try:
        research_context = extract_tool_results(tool_result)
    except Exception as exc:
        return research_failure(exc)

    try:
        structured_result = structured_industry_macro_research_llm.invoke(
            [
                *prompt_value.messages,
                HumanMessage(
                    content=(
                        "Tool results:\n"
                        f"{research_context}\n\n"
                        "Using only these tool results, produce the structured industry "
                        "and macro research result."
                    )
                ),
            ]
        )

        structured_result = require_research_result(
            structured_result, IndustryMacroResearchResult
        )
        return research_success(mark_research_complete(structured_result))
    except Exception as synthesis_error:
        if is_timeout_failure(synthesis_error):
            return research_failure(synthesis_error)
        try:
            fallback_result = build_industry_macro_research_fallback(
                tool_result, ticker=ticker
            )
        except Exception as fallback_error:
            return research_failure(
                RuntimeError(
                    "Structured industry/macro research failed and evidence-backed "
                    "fallback was unavailable. "
                    f"Synthesis error: {type(synthesis_error).__name__}; "
                    f"fallback error: {fallback_error}"
                )
            )
        return research_success(fallback_result)


def build_industry_macro_research_graph():
    builder = StateGraph(
        IndustryMacroResearchState,
        input_schema=IndustryMacroResearchInputState,
        output_schema=IndustryMacroResearchOutputState,
    )

    builder.add_node(
        "industry_macro_research_agent",
        industry_macro_research_agent,
    )

    builder.add_edge(
        START,
        "industry_macro_research_agent",
    )

    builder.add_edge(
        "industry_macro_research_agent",
        END,
    )

    return builder.compile()


industry_macro_research_graph = build_industry_macro_research_graph()