import json
import math
from collections.abc import Mapping
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.agents.models import CompanyResearchResult
from app.agents.research_contracts import mark_research_complete, require_research_result, research_failure, \
    research_success, parse_tool_payloads_by_name, require_nonempty_string, require_finite_number, is_timeout_failure
from app.agents.tool_sets import COMPANY_RESEARCH_TOOLS
from app.graph.tool_loop import build_tool_loop_graph
from app.llm.client import llm


class CompanyResearchInputState(TypedDict):
    ticker: str


class CompanyResearchState(TypedDict):
    ticker: str
    research_result: CompanyResearchResult | None
    research_error: str


class CompanyResearchOutputState(TypedDict):
    research_result: CompanyResearchResult | None
    research_error: str


company_research_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Company Research Agent. "
            "Your responsibility is to research basic company "
            "information for the given stock ticker. "
            "Use the available tools to obtain company name, "
            "sector, and current stock price. "
            "Do not perform valuation. "
            "Do not make an investment recommendation. "
            "Do not assess investment risk. "
            "Do not invent financial data. "
            "The data_status and degradation_reason fields are system-managed; "
            "leave them at their defaults.",
        ),
        (
            "human",
            "Research the following company and return a concise "
            "company research result.\n\n"
            "Ticker: {ticker}",
        ),
    ]
)


structured_company_research_llm = (
    llm.with_structured_output(CompanyResearchResult, method="function_calling")
)

company_research_tool_loop = build_tool_loop_graph(COMPANY_RESEARCH_TOOLS)


def extract_tool_results(tool_result: dict) -> str:
    tool_messages = [
        message
        for message in tool_result["messages"]
        if message.type == "tool"
    ]

    return "\n".join(
        message.content
        for message in tool_messages
    )


def _tool_payloads_by_name(tool_result: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Keep the historical Company Research helper while sharing parsing logic."""
    payloads = parse_tool_payloads_by_name(
        tool_result,
        allowed_names={"get_company_info", "get_stock_price"},
    )
    return {
        name: payload
        for name, payload in payloads.items()
        if isinstance(payload, dict)
    }


def build_company_research_fallback(
    tool_result: Mapping[str, Any],
    *,
    ticker: str,
) -> CompanyResearchResult:
    """Build a degraded result only from validated successful provider outputs.

    This is not a provider fallback: it never invents missing fields and fails
    closed unless both required tools returned evidence for the requested ticker.
    """

    payloads = _tool_payloads_by_name(tool_result)
    company = payloads.get("get_company_info")
    quote = payloads.get("get_stock_price")
    if company is None or quote is None:
        raise ValueError(
            "Fallback requires successful company-info and stock-price tool outputs."
        )
    requested_ticker = ticker.strip().upper()
    if (
        not isinstance(company.get("ticker"), str)
        or company["ticker"].strip().upper() != requested_ticker
        or not isinstance(quote.get("ticker"), str)
        or quote["ticker"].strip().upper() != requested_ticker
    ):
        raise ValueError("Fallback tool outputs do not match the requested ticker.")

    company_name = require_nonempty_string(company.get("company_name"), "company name")
    sector = require_nonempty_string(company.get("sector"), "sector")
    price = require_finite_number(quote.get("price"), "stock price")
    if price <= 0:
        raise ValueError("Fallback stock price must be positive.")

    return CompanyResearchResult(
        ticker=requested_ticker,
        company_name=company_name,
        sector=sector,
        current_price=price,
        summary=(
            "DEGRADED FALLBACK: Structured LLM synthesis was unavailable. "
            f"Provider outputs identify {company_name} as operating in {sector}, "
            f"with a provider-returned share price of {price}."
        ),
        data_status="degraded",
        degradation_reason=(
            "Structured LLM synthesis failed; required fields were assembled "
            "from successful company-info and stock-price tool outputs."
        ),
    )


def company_research_agent(
    state: CompanyResearchState,
) -> CompanyResearchState:

    ticker = state["ticker"]
    prompt_value = company_research_prompt.invoke({"ticker": ticker})

    # Tool/provider failures do not enter the synthesis fallback path.
    try:
        tool_result = company_research_tool_loop.invoke(
            {"messages": prompt_value.messages}
        )
    except Exception as exc:
        return research_failure(exc)

    try:
        research_context = extract_tool_results(tool_result)
    except Exception as exc:
        return research_failure(exc)

    try:
        structured_result = structured_company_research_llm.invoke(
            [
                *prompt_value.messages,
                HumanMessage(
                    content=(
                        "Tool results:\n"
                        f"{research_context}\n\n"
                        "Using only these tool results, produce the structured "
                        "company research result."
                    )
                ),
            ]
        )
        structured_result = require_research_result(
            structured_result, CompanyResearchResult
        )
        return research_success(mark_research_complete(structured_result))
    except Exception as synthesis_error:
        if is_timeout_failure(synthesis_error):
            return research_failure(synthesis_error)
        try:
            fallback_result = build_company_research_fallback(
                tool_result,
                ticker=ticker,
            )
        except Exception as fallback_error:
            return research_failure(
                RuntimeError(
                    "Structured company research failed and evidence-backed "
                    "fallback was unavailable. "
                    f"Synthesis error: {type(synthesis_error).__name__}; "
                    f"fallback error: {fallback_error}"
                )
            )
        return research_success(fallback_result)


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


company_research_graph = build_company_research_graph()