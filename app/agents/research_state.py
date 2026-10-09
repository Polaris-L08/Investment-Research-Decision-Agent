from typing import TypedDict, Annotated

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
    ResearchArea,
    ResearchPlan,
)
from app.valuation import ValuationInputs, ValuationAssumptions


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

    # Produced by the Research stage and consumed by the Application Valuation stage.
    valuation_inputs: ValuationInputs | None
    valuation_assumptions: ValuationAssumptions | None
    valuation_research_error: str

    research_errors: Annotated[dict[str, str], merge_research_errors]

