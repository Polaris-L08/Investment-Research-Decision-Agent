from typing import TypedDict, Annotated

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
    ResearchArea,
    ResearchPlan,
)


def merge_research_errors(
    existing: dict[str, str] | None,
    new: dict[str, str] | None,
) -> dict[str, str]:
    """Merge research errors from parallel research agents."""
    merged = dict(existing or {})
    merged.update(new or {})
    return merged


class ResearchState(TypedDict, total=False):
    """Shared state boundary for multi-agent research orchestration."""

    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea

    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None

    research_errors: Annotated[dict[str, str], merge_research_errors]

