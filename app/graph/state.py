from typing import Literal, TypedDict


Recommendation = Literal[
    "Strong Buy",
    "Buy",
    "Hold",
    "Reduce",
    "Sell",
]

InvestmentHorizon = Literal[
    "Short Term",
    "Medium Term",
    "Long Term",
]

class InputState(TypedDict):
    user_query: str
    ticker: str

class GraphState(TypedDict):
    # User request
    user_query: str
    ticker: str

    # Research planning
    research_plan: list[str]

    # Research results
    company_research: str
    financial_research: str
    market_research: str
    industry_research: str

    # Valuation
    valuation_summary: str
    current_price: float
    target_price: float

    # Risk analysis
    risk_factors: list[str]

    # Investment decision
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    investment_thesis: str

    llm_response: str

class OutputState(TypedDict):
    ticker: str
    recommendation: Recommendation
    investment_horizon: InvestmentHorizon
    current_price: float
    target_price: float
    investment_thesis: str