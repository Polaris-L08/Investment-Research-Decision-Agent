from enum import Enum
from math import isclose

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvestmentRecommendation(str, Enum):
    """Investment recommendation."""

    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    REDUCE = "Reduce"
    SELL = "Sell"


class InvestmentHorizon(str, Enum):
    """Expected investment holding horizon."""

    SHORT_TERM = "Short Term"
    MEDIUM_TERM = "Medium Term"
    LONG_TERM = "Long Term"


class InvestmentConviction(str, Enum):
    """Confidence level in the investment decision."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class InvestmentDecision(BaseModel):
    """Structured investment decision produced from research, valuation, and risk analysis."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        min_length=1,
        description="Stock ticker symbol.",
    )

    recommendation: InvestmentRecommendation = Field(
        description="Investment recommendation.",
    )

    investment_horizon: InvestmentHorizon = Field(
        description="Expected investment holding horizon.",
    )

    current_price: float = Field(
        gt=0,
        description="Current stock price used by the decision.",
    )

    target_price: float = Field(
        gt=0,
        description="Target price used by the decision.",
    )

    expected_upside: float = Field(
        description=(
            "Expected upside/downside expressed as a decimal. "
            "Must equal (target_price - current_price) / current_price."
        ),
    )

    conviction: InvestmentConviction = Field(
        description="Confidence level in the investment decision.",
    )

    investment_thesis: str = Field(
        min_length=1,
        description="Core rationale supporting the investment decision.",
    )

    key_catalysts: list[str] = Field(
        min_length=1,
        description="Important factors that could improve the investment outcome.",
    )

    key_risks: list[str] = Field(
        min_length=1,
        description="Important risks that could impair the investment thesis.",
    )

    invalidation_conditions: list[str] = Field(
        min_length=1,
        description="Conditions that would invalidate the investment thesis.",
    )

    supporting_evidence: list[str] = Field(
        min_length=1,
        description="Evidence supporting the investment decision.",
    )

    @model_validator(mode="after")
    def validate_expected_upside(self) -> "InvestmentDecision":
        """Ensure expected upside is mathematically consistent with prices."""

        calculated_upside = (
            self.target_price - self.current_price
        ) / self.current_price

        if not isclose(
            self.expected_upside,
            calculated_upside,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                "expected_upside must equal "
                "(target_price - current_price) / current_price"
            )

        return self