from typing import TypedDict

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
    ResearchArea,
    ResearchPlan,
)


class ResearchState(TypedDict, total=False):
    """Shared state boundary for multi-agent research orchestration."""

    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea

    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None

    research_errors: dict[str, str]
