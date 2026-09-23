import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.graph.models import ResearchSummary, InvestmentDecision, Recommendation, InvestmentHorizon
from app.graph.state import GraphState, InputState, OutputState


load_dotenv()


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0,
)

structured_llm = llm.with_structured_output(ResearchSummary)


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


def initialize_state(state: InputState) -> GraphState:
    return {
        "user_query": state["user_query"],
        "ticker": state["ticker"],
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
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
        )
    }


def llm_node(state: GraphState) -> GraphState:
    prompt_value = llm_prompt.invoke(
        {
            "ticker": state["ticker"],
            "user_query": state["user_query"],
        }
    )

    response = structured_llm.invoke(prompt_value)

    return {
        "research_summary": response,
    }


def create_research_plan(state: GraphState) -> GraphState:
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


def prepare_output(state: GraphState) -> OutputState:
    return {
        "ticker": state["ticker"],
        "recommendation": state["recommendation"],
        "investment_horizon": state["investment_horizon"],
        "current_price": state["current_price"],
        "target_price": state["target_price"],
        "investment_thesis": state["investment_thesis"],
    }


builder = StateGraph(
    GraphState,
    input_schema=InputState,
    output_schema=OutputState,
)

builder.add_node("initialize_state", initialize_state)
builder.add_node("llm_node", llm_node)
builder.add_node("create_research_plan", create_research_plan)
builder.add_node("prepare_output", prepare_output)

builder.add_edge(START, "initialize_state")
builder.add_edge("initialize_state", "llm_node")
builder.add_edge("llm_node", "create_research_plan")
builder.add_edge("create_research_plan", "prepare_output")
builder.add_edge("prepare_output", END)

graph = builder.compile()