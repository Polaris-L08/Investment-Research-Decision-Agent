from pydantic import BaseModel, Field
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


class CompanyResearchResult(BaseModel):
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


class FinancialResearchResult(BaseModel):
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


class MarketResearchResult(BaseModel):
    ticker: str
    market_index: str
    market_return: float
    summary: str


class IndustryMacroResearchResult(BaseModel):
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