from langgraph.graph import END, START, StateGraph

from app.graph.state import GraphState, InputState, OutputState


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
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "investment_thesis": "",
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
builder.add_node("create_research_plan", create_research_plan)
builder.add_node("prepare_output", prepare_output)

builder.add_edge(START, "initialize_state")
builder.add_edge("initialize_state", "create_research_plan")
builder.add_edge("create_research_plan", "prepare_output")
builder.add_edge("prepare_output", END)

graph = builder.compile()