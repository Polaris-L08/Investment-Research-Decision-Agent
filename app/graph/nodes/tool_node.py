from app.tools.financial import get_stock_price


def get_stock_price_node(state):
    ticker = state["ticker"]

    try:
        result = get_stock_price.invoke(
            {"ticker": ticker}
        )

        return {
            "current_price": result["price"],
            "tool_error": None,
        }

    except ValueError as exc:
        return {
            "tool_error": str(exc),
        }