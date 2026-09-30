from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RiskCategory(str, Enum):
    """Categories used to classify investment risks."""

    COMPANY = "Company"
    OPERATIONAL = "Operational"
    FINANCIAL = "Financial"
    MARKET = "Market"
    VALUATION = "Valuation"
    INDUSTRY = "Industry"
    MACRO = "Macro"
    REGULATORY = "Regulatory"
    DATA_UNCERTAINTY = "Data Uncertainty"


class RiskSeverity(str, Enum):
    """Severity of the potential effect on the investment thesis."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskLikelihood(str, Enum):
    """Estimated likelihood that a risk materializes."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskImpact(str, Enum):
    """Potential impact of a risk on the investment thesis."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskItem(BaseModel):
    """A single structured investment risk."""

    model_config = ConfigDict(extra="forbid")

    category: RiskCategory = Field(
        description="Category of the investment risk.",
    )

    title: str = Field(
        min_length=1,
        description="Short title describing the risk.",
    )

    description: str = Field(
        min_length=1,
        description="Explanation of how the risk could affect the investment thesis.",
    )

    severity: RiskSeverity = Field(
        description="Overall severity of the risk.",
    )

    likelihood: RiskLikelihood = Field(
        description="Estimated likelihood of the risk materializing.",
    )

    impact: RiskImpact = Field(
        description="Potential impact on the investment thesis if the risk materializes.",
    )

    evidence: list[str] = Field(
        min_length=1,
        description="Evidence supporting the identification of this risk.",
    )


class RiskAnalysis(BaseModel):
    """Structured risk analysis for an investment thesis."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        min_length=1,
        description="Stock ticker symbol.",
    )

    risks: list[RiskItem] = Field(
        description="Structured list of identified investment risks.",
    )

    overall_risk_level: RiskSeverity = Field(
        description="Overall risk level assigned to the investment case.",
    )

    key_risks: list[str] = Field(
        description="Titles of the most important risks for the investment case.",
    )

    uncertainty_notes: list[str] = Field(
        description="Important uncertainties or limitations in the available evidence.",
    )