from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agents.models import IndustryMacroResearchResult
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
            "Do not invent industry or macroeconomic data.",
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
    IndustryMacroResearchResult
)


def extract_tool_results(tool_result: dict) -> str:
    tool_messages = [
        message
        for message in tool_result["messages"]
        if message.type == "tool"
    ]

    return "\n".join(message.content for message in tool_messages)


def industry_macro_research_agent(
    state: IndustryMacroResearchState,
) -> IndustryMacroResearchState:
    ticker = state["ticker"]

    prompt_value = industry_macro_research_prompt.invoke(
        {"ticker": ticker}
    )

    try:
        tool_result = industry_macro_research_tool_loop.invoke(
            {"messages": prompt_value.messages}
        )

        research_context = extract_tool_results(tool_result)

        structured_result = (
            structured_industry_macro_research_llm.invoke(
                [
                    *prompt_value.messages,
                    HumanMessage(
                        content=(
                            "Tool results:\n"
                            f"{research_context}\n\n"
                            "Using only these tool results, "
                            "produce the structured industry and "
                            "macro research result."
                        )
                    ),
                ]
            )
        )

    except Exception as exc:
        return {
            "ticker": ticker,
            "research_result": None,
            "research_error": str(exc),
        }

    return {
        "ticker": ticker,
        "research_result": structured_result,
        "research_error": "",
    }


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