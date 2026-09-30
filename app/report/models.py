from pydantic import BaseModel, ConfigDict, Field

from app.investment.models import InvestmentDecision
from app.risk.models import RiskAnalysis
from app.valuation.models import ValuationResult


class InvestmentReport(BaseModel):
    """
    Domain model representing a complete investment research report.

    The report composes existing domain results instead of duplicating
    business facts owned by other domains.
    """

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        min_length=1,
        description="Stock ticker symbol.",
    )

    title: str = Field(
        min_length=1,
        description="Report title.",
    )

    executive_summary: str = Field(
        min_length=1,
        description="Executive summary of the investment research.",
    )

    company_overview: str = Field(
        min_length=1,
        description="Narrative overview of the company.",
    )

    financial_summary: str = Field(
        min_length=1,
        description="Narrative summary of the company's financials.",
    )

    market_summary: str = Field(
        min_length=1,
        description="Narrative summary of the market environment.",
    )

    industry_macro_summary: str = Field(
        min_length=1,
        description="Narrative summary of industry and macro conditions.",
    )

    valuation_summary: str = Field(
        min_length=1,
        description="Narrative summary of the valuation analysis.",
    )

    risk_summary: str = Field(
        min_length=1,
        description="Narrative summary of the risk analysis.",
    )

    investment_decision_summary: str = Field(
        min_length=1,
        description="Narrative summary of the investment decision.",
    )

    valuation: ValuationResult = Field(
        description="Valuation result used as the source of truth for valuation facts.",
    )

    risk_analysis: RiskAnalysis = Field(
        description="Risk analysis used as the source of truth for risk facts.",
    )

    investment_decision: InvestmentDecision = Field(
        description="Investment decision used as the source of truth for decision facts.",
    )