from enum import Enum

from pydantic import BaseModel, Field


class Recommendation(str, Enum):
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    REDUCE = "Reduce"
    SELL = "Sell"


class InvestmentHorizon(str, Enum):
    SHORT_TERM = "Short Term"
    MEDIUM_TERM = "Medium Term"
    LONG_TERM = "Long Term"


class ResearchSummary(BaseModel):
    summary: str = Field(
        description="A concise summary of the investment research."
    )

    key_factors: list[str] = Field(
        description="The key factors that materially affect the investment analysis."
    )


class InvestmentDecision(BaseModel):
    recommendation: Recommendation = Field(
        description="The investment recommendation."
    )

    investment_horizon: InvestmentHorizon = Field(
        description="The expected investment horizon."
    )

    investment_thesis: str = Field(
        description="The concise investment thesis supporting the recommendation."
    )