from typing import Literal

from pydantic import BaseModel, Field, model_validator
from enum import Enum


class ResearchArea(str, Enum):
    COMPANY = "company"
    FINANCIAL = "financial"
    MARKET = "market"
    INDUSTRY_MACRO = "industry_macro"


class ResearchPlan(BaseModel):
    research_areas: list[ResearchArea] = Field(
        description=(
            "The research areas required to answer the "
            "user's research request."
        )
    )
    rationale: str = Field(
        description=(
            "A concise explanation of why these research "
            "areas are required."
        )
    )


class ResearchResultBase(BaseModel):
    """Shared provenance/status contract for every research-area result.

    Status is operational metadata, not an LLM-authored conclusion.
    Complete results have no degradation reason; degraded results must explain
    the limitation explicitly.
    """

    data_status: Literal["complete", "degraded"] = Field(
        default="complete",
        description="Whether this result followed the normal or degraded path.",
    )
    degradation_reason: str = Field(
        default="",
        description="Why this result is degraded; empty for complete results.",
    )

    @model_validator(mode="after")
    def validate_degradation_metadata(self):
        reason = self.degradation_reason.strip()
        object.__setattr__(self, "degradation_reason", reason)
        if self.data_status == "degraded" and not reason:
            raise ValueError("A degraded research result requires degradation_reason.")
        if self.data_status == "complete" and reason:
            raise ValueError("A complete research result must not have degradation_reason.")
        return self


class CompanyResearchResult(ResearchResultBase):
    ticker: str = Field(
        description="Stock ticker symbol."
    )

    company_name: str = Field(
        description="Company name."
    )

    sector: str = Field(
        description="Primary business sector."
    )

    current_price: float = Field(
        description="Current stock price."
    )

    summary: str = Field(
        description="Concise factual company research summary."
    )


class FinancialResearchResult(ResearchResultBase):
    ticker: str = Field(
        description="Stock ticker symbol."
    )

    revenue: float = Field(
        description="Company revenue."
    )

    net_income: float = Field(
        description="Company net income."
    )

    profit_margin: float = Field(
        description="Net income divided by revenue."
    )

    summary: str = Field(
        description="Concise factual financial research summary."
    )


class MarketResearchResult(ResearchResultBase):
    ticker: str
    market_index: str
    market_return: float
    summary: str


class IndustryMacroResearchResult(ResearchResultBase):
    ticker: str = Field(description="Stock ticker symbol.")
    industry: str = Field(description="Industry associated with the company.")
    industry_growth: float = Field(
        description="Industry growth rate."
    )
    macro_environment: str = Field(
        description="Current macroeconomic environment."
    )
    macro_growth: float = Field(
        description="Macro-level growth rate."
    )
    summary: str = Field(
        description="Concise factual industry and macro research summary."
    )