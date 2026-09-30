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


def calculate_target_price(implied_value_per_share: float) -> float:
    """Convert the valuation model's implied value into the target price."""

    if implied_value_per_share <= 0:
        raise ValueError("Implied value per share must be positive.")

    return implied_value_per_share


def calculate_expected_upside(
    target_price: float,
    current_price: float,
) -> float:
    """Calculate expected upside/downside from target and current prices.

    Formula:
        (target price - current price) / current price
    """

    if target_price <= 0:
        raise ValueError("Target price must be positive.")

    if current_price <= 0:
        raise ValueError("Current price must be positive.")

    return (target_price - current_price) / current_price