def calculate_profit_margin(
    revenue: float,
    net_income: float,
) -> float:
    """Calculate profit margin deterministically.

    Formula:
        profit margin = net income / revenue
    """

    if revenue <= 0:
        raise ValueError("Revenue must be positive.")

    return net_income / revenue
