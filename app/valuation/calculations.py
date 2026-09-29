from app.valuation.models import ValuationAssumptions, ValuationInputs


def calculate_pe_implied_value(
    inputs: ValuationInputs,
    assumptions: ValuationAssumptions,
) -> float:
    """Calculate implied value per share using the P/E valuation method.

    Formula:
        implied value per share = earnings per share × assumed P/E multiple

    The function is intentionally deterministic and has no LLM, provider,
    network, or LangGraph dependency.
    """

    return inputs.earnings_per_share * assumptions.multiple