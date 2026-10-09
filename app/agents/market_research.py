from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agents.models import MarketResearchResult
from app.agents.research_contracts import require_research_result, research_failure, research_success
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
            "Do not invent market data.",
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
    MarketResearchResult
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


def market_research_agent(
    state: MarketResearchState,
) -> MarketResearchState:

    ticker = state["ticker"]

    prompt_value = market_research_prompt.invoke(
        {
            "ticker": ticker,
        }
    )

    try:
        tool_result = market_research_tool_loop.invoke(
            {
                "messages": prompt_value.messages,
            }
        )

        research_context = extract_tool_results(
            tool_result
        )

        structured_result = (
            structured_market_research_llm.invoke(
                [
                    *prompt_value.messages,
                    HumanMessage(
                        content=(
                            "Tool results:\n"
                            f"{research_context}\n\n"
                            "Using only these tool results, "
                            "produce the structured market "
                            "research result."
                        )
                    ),
                ]
            )
        )

        structured_result = require_research_result(
            structured_result,
            MarketResearchResult,
        )

    except Exception as exc:
        return research_failure(exc)

    return research_success(structured_result)


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