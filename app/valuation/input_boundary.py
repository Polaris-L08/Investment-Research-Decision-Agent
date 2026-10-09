"""Validation boundary for data required by the valuation model.

The caller must supply EPS and the valuation multiple assumption explicitly.
This module deliberately does not infer EPS from revenue/net income or invent
assumptions. A future production provider integration may populate these
contracts, but it must still pass through this boundary.
"""

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import Any

from app.agents.models import CompanyResearchResult
from app.valuation.models import ValuationAssumptions, ValuationInputs


class ValuationInputError(ValueError):
    """Raised when required valuation inputs are missing or inconsistent."""


@dataclass(frozen=True)
class ValidatedValuationInputs:
    """Typed, validated values that the deterministic valuation model consumes."""

    ticker: str
    company_research: CompanyResearchResult
    valuation_inputs: ValuationInputs
    valuation_assumptions: ValuationAssumptions


def validate_valuation_input_boundary(
    state: Mapping[str, Any],
) -> ValidatedValuationInputs:
    """Validate required valuation inputs without applying hidden defaults."""

    ticker = state.get("ticker")
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValuationInputError("Ticker is required for valuation.")
    ticker = ticker.strip().upper()

    company_research = state.get("company_research")
    if not isinstance(company_research, CompanyResearchResult):
        raise ValuationInputError(
            "Valid company research is required for the current share price."
        )

    if company_research.ticker.strip().upper() != ticker:
        raise ValuationInputError(
            "Ticker mismatch between Application request and company research: "
            f"requested '{ticker}', received '{company_research.ticker}'."
        )

    if not math.isfinite(company_research.current_price) or company_research.current_price <= 0:
        raise ValuationInputError(
            "Company research current_price must be a finite positive number."
        )

    valuation_inputs = state.get("valuation_inputs")
    if not isinstance(valuation_inputs, ValuationInputs):
        raise ValuationInputError(
            "Explicit ValuationInputs are required; EPS will not be inferred "
            "from other research fields."
        )

    if not math.isfinite(valuation_inputs.earnings_per_share):
        raise ValuationInputError("Earnings per share must be finite.")

    valuation_assumptions = state.get("valuation_assumptions")
    if not isinstance(valuation_assumptions, ValuationAssumptions):
        raise ValuationInputError(
            "Explicit ValuationAssumptions are required; valuation multiples "
            "will not be silently defaulted."
        )

    if not math.isfinite(valuation_assumptions.multiple):
        raise ValuationInputError("Valuation multiple must be finite.")

    if not valuation_assumptions.rationale.strip():
        raise ValuationInputError(
            "Valuation assumption rationale must not be empty."
        )

    return ValidatedValuationInputs(
        ticker=ticker,
        company_research=company_research,
        valuation_inputs=valuation_inputs,
        valuation_assumptions=valuation_assumptions,
    )
