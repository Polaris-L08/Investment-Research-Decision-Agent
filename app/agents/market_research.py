from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agents.models import MarketResearchResult
from app.agents.research_contracts import require_research_result, research_failure, research_success, \
    require_tool_calls_match_ticker, parse_tool_payloads_by_name, require_nonempty_string, require_finite_number, \
    mark_research_complete, is_timeout_failure
from app.agents.tool_sets import MARKET_RESEARCH_TOOLS
from app.graph.tool_loop import build_tool_loop_graph
from app.llm.client import llm


class MarketResearchInputState(TypedDict):
    ticker: str


class MarketResearchState(TypedDict):
    ticker: str
    research_result: MarketResearchResult | None
    research_error: str


class MarketResearchOutputState(TypedDict):
    research_result: MarketResearchResult | None
    research_error: str


market_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Market Research Agent. "
            "Your responsibility is to research basic market "
            "conditions for the given stock ticker. "
            "Use the available tools to obtain the relevant "
            "market index and market return. "
            "Return a concise factual market research result. "
            "Do not perform company financial analysis. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent market data. "
            "The data_status and degradation_reason fields are system-managed; "
            "leave them at their defaults.",
        ),
        (
            "human",
            "Research the market conditions associated with "
            "the following company.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)


market_research_tool_loop = build_tool_loop_graph(
    MARKET_RESEARCH_TOOLS
)


structured_market_research_llm = llm.with_structured_output(
    MarketResearchResult,
    method="function_calling"
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


def build_market_research_fallback(
    tool_result: dict, *, ticker: str
) -> MarketResearchResult:
    """Build a degraded market result from actual index/return tool data."""
    required_tools = {"get_market_index", "get_market_return"}
    require_tool_calls_match_ticker(tool_result, ticker, required_tools)
    payloads = parse_tool_payloads_by_name(tool_result, allowed_names=required_tools)
    if not required_tools.issubset(payloads):
        raise ValueError("Fallback requires successful market-index and market-return tool outputs.")
    market_index = require_nonempty_string(payloads["get_market_index"], "market index")
    market_return = require_finite_number(payloads["get_market_return"], "market return")
    return MarketResearchResult(
        ticker=ticker.strip().upper(),
        market_index=market_index,
        market_return=market_return,
        summary=(
            "DEGRADED FALLBACK: Structured LLM synthesis was unavailable. "
            f"Provider outputs returned market index {market_index} and market return "
            f"{market_return}."
        ),
        data_status="degraded",
        degradation_reason=(
            "Structured LLM synthesis failed; market index and market return were "
            "retained from successful tool outputs without adding a market interpretation."
        ),
    )


def market_research_agent(state: MarketResearchState) -> MarketResearchState:
    ticker = state["ticker"]
    prompt_value = market_research_prompt.invoke({"ticker": ticker})
    try:
        tool_result = market_research_tool_loop.invoke({"messages": prompt_value.messages})
    except Exception as exc:
        return research_failure(exc)

    try:
        research_context = extract_tool_results(tool_result)
    except Exception as exc:
        return research_failure(exc)

    try:
        structured_result = structured_market_research_llm.invoke(
            [
                *prompt_value.messages,
                HumanMessage(
                    content=(
                        "Tool results:\n"
                        f"{research_context}\n\n"
                        "Using only these tool results, produce the structured market "
                        "research result."
                    )
                ),
            ]
        )
        structured_result = require_research_result(structured_result, MarketResearchResult)
        return research_success(mark_research_complete(structured_result))
    except Exception as synthesis_error:
        if is_timeout_failure(synthesis_error):
            return research_failure(synthesis_error)
        try:
            fallback_result = build_market_research_fallback(tool_result, ticker=ticker)
        except Exception as fallback_error:
            return research_failure(
                RuntimeError(
                    "Structured market research failed and evidence-backed fallback "
                    "was unavailable. "
                    f"Synthesis error: {type(synthesis_error).__name__}; "
                    f"fallback error: {fallback_error}"
                )
            )
        return research_success(fallback_result)


def build_market_research_graph():
    builder = StateGraph(
        MarketResearchState,
        input_schema=MarketResearchInputState,
        output_schema=MarketResearchOutputState,
    )

    builder.add_node(
        "market_research_agent",
        market_research_agent,
    )

    builder.add_edge(
        START,
        "market_research_agent",
    )

    builder.add_edge(
        "market_research_agent",
        END,
    )

    return builder.compile()


market_research_graph = build_market_research_graph()