from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.company_research import company_research_graph
from app.graph.checkpointer import create_checkpointer
from app.graph.models import (
    InvestmentDecision,
    InvestmentHorizon,
    Recommendation,
    ResearchSummary,
)
from app.graph.nodes.tool_node import get_stock_price_node
from app.graph.state import (
    GraphState,
    InputState,
    OutputState,
)
from app.llm.client import llm


MAX_LLM_RETRIES = 2


structured_research_llm = (
    llm.with_structured_output(ResearchSummary)
)

structured_decision_llm = (
    llm.with_structured_output(InvestmentDecision)
)


llm_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an investment research assistant. "
            "Provide concise and factual research guidance.",
        ),
        (
            "human",
            "Analyze the following investment research request.\n\n"
            "Ticker: {ticker}\n"
            "User request: {user_query}",
        ),
    ]
)


decision_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an investment decision assistant. "
            "Make a structured investment decision based on the "
            "provided research summary. "
            "Use only the allowed recommendation and investment "
            "horizon values.",
        ),
        (
            "human",
            "Make an investment decision for the following company.\n\n"
            "Ticker: {ticker}\n"
            "User request: {user_query}\n\n"
            "Research summary:\n"
            "{research_summary}\n\n"
            "Key factors:\n"
            "{key_factors}",
        ),
    ]
)


def initialize_state(
    state: InputState,
) -> GraphState:

    return {
        "user_query": state["user_query"],
        "ticker": state["ticker"],

        "research_plan": [],

        "company_research": "",
        "company_research_result": None,
        "financial_research": "",
        "market_research": "",
        "industry_research": "",

        "valuation_summary": "",
        "current_price": None,
        "target_price": 0.0,
        "risk_factors": [],

        "recommendation": Recommendation.HOLD,
        "investment_horizon": InvestmentHorizon.LONG_TERM,
        "investment_thesis": "",

        "llm_response": "",

        "research_summary": ResearchSummary(
            summary="",
            key_factors=[],
        ),

        "investment_decision": InvestmentDecision(
            recommendation=Recommendation.HOLD,
            investment_horizon=InvestmentHorizon.LONG_TERM,
            investment_thesis="",
        ),

        "llm_error": "",
        "failure_reason": "",
        "retry_count": 0,

        "tool_error": None,
        "tool_retry_count": 0,
        "tool_retryable": False,
    }


def company_research_node(
    state: GraphState,
) -> GraphState:

    result = company_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    research_result = result["research_result"]
    research_error = result["research_error"]

    if research_error:
        return {
            "company_research_result": None,
            "current_price": None,
            "failure_reason": (
                "Company research failed: "
                f"{research_error}"
            ),
        }

    return {
        "company_research_result": research_result,
        "current_price": research_result.current_price,
        "failure_reason": "",
    }


def route_after_company_research(
    state: GraphState,
) -> str:

    if state["failure_reason"]:
        return "failure"

    return "continue"


def handle_company_research_failure(
    state: GraphState,
) -> GraphState:

    return {
        "failure_reason": state["failure_reason"],
    }


def llm_node(
    state: GraphState,
) -> GraphState:

    prompt_value = llm_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
        }
    )

    try:
        response = structured_research_llm.invoke(
            prompt_value
        )

    except Exception as exc:
        return {
            "llm_error": str(exc),
        }

    return {
        "research_summary": response,
        "llm_error": "",
    }


def investment_decision_node(
    state: GraphState,
) -> GraphState:

    prompt_value = decision_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
            "research_summary": (
                state["research_summary"].summary
            ),
            "key_factors": ", ".join(
                state["research_summary"].key_factors
            ),
        }
    )

    try:
        response = structured_decision_llm.invoke(
            prompt_value
        )

    except Exception as exc:
        return {
            "llm_error": str(exc),
        }

    return {
        "investment_decision": response,
        "llm_error": "",
    }


def route_after_llm(
    state: GraphState,
) -> str:

    if not state["llm_error"]:
        return "continue"

    if state["retry_count"] < MAX_LLM_RETRIES:
        return "retry"

    return "llm_failure"


def route_after_decision(
    state: GraphState,
) -> str:

    if state["llm_error"]:
        return "llm_failure"

    return "continue"


def handle_llm_failure(
    state: GraphState,
) -> GraphState:

    return {
        "failure_reason": (
            "LLM structured output failed: "
            f"{state['llm_error']}"
        ),
    }


def handle_tool_failure(
    state: GraphState,
) -> GraphState:

    return {
        "failure_reason": (
            "Tool execution failed: "
            f"{state['tool_error']}"
        )
    }


def retry_llm(
    state: GraphState,
) -> GraphState:

    return {
        "retry_count": state["retry_count"] + 1,
        "llm_error": "",
    }


def create_research_plan(
    state: GraphState,
) -> GraphState:

    return {
        "research_plan": [
            "Analyze company fundamentals",
            "Review financial performance",
            "Analyze market conditions",
            "Analyze industry conditions",
            "Perform valuation analysis",
            "Identify major risks",
        ],
    }


def prepare_output(
    state: GraphState,
) -> OutputState:

    decision = state["investment_decision"]

    return {
        "ticker": state["ticker"],
        "recommendation": decision.recommendation,
        "investment_horizon": decision.investment_horizon,
        "current_price": state["current_price"],
        "target_price": state["target_price"],
        "investment_thesis": (
            decision.investment_thesis
        ),
        "failure_reason": state["failure_reason"],
    }


def prepare_failure_output(
    state: GraphState,
) -> OutputState:

    return {
        "ticker": state["ticker"],
        "recommendation": state["recommendation"],
        "investment_horizon": state["investment_horizon"],
        "current_price": state["current_price"],
        "target_price": state["target_price"],
        "investment_thesis": state["investment_thesis"],
        "failure_reason": state["failure_reason"],
    }


def build_graph(checkpointer=None):
    builder = StateGraph(
        GraphState,
        input_schema=InputState,
        output_schema=OutputState,
    )


    builder.add_node(
        "initialize_state",
        initialize_state,
    )

    builder.add_node(
        "company_research",
        company_research_node,
    )

    builder.add_node(
        "company_research_failure",
        handle_company_research_failure,
    )

    builder.add_node(
        "llm_node",
        llm_node,
    )

    builder.add_node(
        "retry_llm",
        retry_llm,
    )

    builder.add_node(
        "handle_llm_failure",
        handle_llm_failure,
    )

    builder.add_node(
        "get_stock_price",
        get_stock_price_node,
    )

    builder.add_node(
        "create_research_plan",
        create_research_plan,
    )

    builder.add_node(
        "investment_decision_node",
        investment_decision_node,
    )

    builder.add_node(
        "prepare_output",
        prepare_output,
    )

    builder.add_node(
        "prepare_failure_output",
        prepare_failure_output,
    )


    builder.add_edge(
        START,
        "initialize_state",
    )

    builder.add_edge(
        "initialize_state",
        "company_research",
    )


    builder.add_conditional_edges(
        "company_research",
        route_after_company_research,
        {
            "continue": "llm_node",
            "failure": "company_research_failure",
        },
    )


    builder.add_edge(
        "company_research_failure",
        "prepare_failure_output",
    )


    builder.add_conditional_edges(
        "llm_node",
        route_after_llm,
        {
            "continue": "create_research_plan",
            "retry": "retry_llm",
            "llm_failure": "handle_llm_failure",
        },
    )


    builder.add_conditional_edges(
        "investment_decision_node",
        route_after_decision,
        {
            "continue": "prepare_output",
            "llm_failure": "handle_llm_failure",
        },
    )


    builder.add_edge(
        "retry_llm",
        "llm_node",
    )

    builder.add_edge(
        "create_research_plan",
        "investment_decision_node",
    )

    builder.add_edge(
        "handle_llm_failure",
        "prepare_failure_output",
    )

    builder.add_edge(
        "prepare_output",
        END,
    )

    builder.add_edge(
        "prepare_failure_output",
        END,
    )

    return builder.compile(checkpointer=checkpointer)

graph = build_graph()