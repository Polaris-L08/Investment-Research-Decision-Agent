from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReportSectionId(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    COMPANY_OVERVIEW = "company_overview"
    FINANCIAL_SUMMARY = "financial_summary"
    MARKET_SUMMARY = "market_summary"
    INDUSTRY_MACRO_SUMMARY = "industry_macro_summary"
    VALUATION_SUMMARY = "valuation_summary"
    RISK_SUMMARY = "risk_summary"
    INVESTMENT_DECISION_SUMMARY = "investment_decision_summary"


class ReportSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: ReportSectionId
    content: str = Field(
        min_length=1,
        description="Human-readable narrative content for the report section.",
    )


class ReportNarrativeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: list[ReportSection] = Field(
        min_length=1,
        description="Generated report narrative sections.",
    )