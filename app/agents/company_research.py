from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.graph.graph import llm
from app.graph.tool_loop import build_tool_loop_graph


class CompanyResearchResult(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol."
    )

    company_name: str = Field(
        description="Legal or commonly used company name."
    )

    sector: str = Field(
        description="Primary business sector."
    )

    current_price: float = Field(
        description="Current stock price."
    )

    summary: str = Field(
        description="Concise factual company research summary."
    )


company_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Company Research Agent. "
            "Your responsibility is to research basic company information "
            "for the given stock ticker. "
            "Use the available tools to obtain company name, sector, and "
            "current stock price. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent financial data.",
        ),
        (
            "human",
            "Research the following company and return a concise company "
            "research result.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)


structured_company_research_llm = llm.with_structured_output(
    CompanyResearchResult
)


class CompanyResearchInputState(TypedDict):
    ticker: str


class CompanyResearchState(TypedDict):
    ticker: str
    research_result: CompanyResearchResult | None
    research_error: str


class CompanyResearchOutputState(TypedDict):
    research_result: CompanyResearchResult | None
    research_error: str


def company_research_agent(
    state: CompanyResearchState,
) -> CompanyResearchState:
    ticker = state["ticker"]

    prompt_value = company_research_prompt.invoke(
        {
            "ticker": ticker,
        }
    )

    try:
        tool_loop = build_tool_loop_graph()

        tool_result = tool_loop.invoke(
            {
                "messages": [
                    *prompt_value.messages
                ]
            }
        )

        research_context = "\n".join(
            message.content
            for message in tool_result["messages"]
            if message.type == "tool"
        )

        structured_result = structured_company_research_llm.invoke(
            [
                *prompt_value.messages,
                HumanMessage(
                    content=(
                        "Tool results:\n"
                        f"{research_context}\n\n"
                        "Using only these tool results, produce the "
                        "structured company research result."
                    )
                ),
            ]
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


def build_company_research_graph():
    builder = StateGraph(
        CompanyResearchState,
        input_schema=CompanyResearchInputState,
        output_schema=CompanyResearchOutputState,
    )

    builder.add_node(
        "company_research_agent",
        company_research_agent,
    )

    builder.add_edge(
        START,
        "company_research_agent",
    )

    builder.add_edge(
        "company_research_agent",
        END,
    )

    return builder.compile()