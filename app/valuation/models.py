from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ValuationMethod(str, Enum):
    """Supported valuation methodologies."""

    PE = "P/E"


class ValuationInputs(BaseModel):
    """Numerical inputs consumed by a valuation model."""

    model_config = ConfigDict(extra="forbid")

    earnings_per_share: float = Field(
        gt=0,
        description="Earnings per share used by the valuation model.",
    )


class ValuationAssumptions(BaseModel):
    """Explicit assumptions used to determine the valuation multiple."""

    model_config = ConfigDict(extra="forbid")

    multiple: float = Field(
        gt=0,
        description="Valuation multiple assumed by the analyst.",
    )
    rationale: str = Field(
        min_length=1,
        description="Reason for selecting the valuation multiple.",
    )


class ValuationMetadata(BaseModel):
    """Metadata describing how a valuation result was produced."""

    model_config = ConfigDict(extra="forbid")

    currency: str = Field(
        min_length=1,
        description="Currency of the per-share valuation result.",
    )
    model_version: str = Field(
        min_length=1,
        description="Version identifier of the valuation model.",
    )


class ValuationResult(BaseModel):
    """Structured output of a valuation model."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        min_length=1,
        description="Stock ticker symbol.",
    )
    method: ValuationMethod = Field(
        description="Valuation methodology used.",
    )
    inputs: ValuationInputs = Field(
        description="Numerical inputs used by the model.",
    )
    assumptions: ValuationAssumptions = Field(
        description="Explicit assumptions used by the model.",
    )
    implied_value_per_share: float = Field(
        gt=0,
        description="Implied per-share value produced by the model.",
    )
    target_price: float = Field(
        gt=0,
        description="Target price derived from the valuation result.",
    )
    current_price: float = Field(
        gt=0,
        description="Current stock price used for return calculation.",
    )
    expected_upside: float = Field(
        description=(
            "Expected upside/downside expressed as a decimal, "
            "calculated from target price and current price."
        ),
    )
    metadata: ValuationMetadata = Field(
        description="Metadata describing the valuation result.",
    )