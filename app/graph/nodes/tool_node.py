from app.tools.financial import (
    TransientToolError,
    get_stock_price,
)

MAX_TOOL_RETRIES = 2

def get_stock_price_node(state):
    ticker = state["ticker"]
    retry_count = state["tool_retry_count"]

    try:
        result = get_stock_price.invoke(
            {"ticker": ticker}
        )

        return {
            "current_price": result["price"],
            "tool_error": None,
            "tool_retryable": False,
        }

    except TransientToolError as exc:
        return {
            "tool_error": str(exc),
            "tool_retryable": True,
            "tool_retry_count": retry_count + 1,
        }

    except ValueError as exc:
        return {
            "tool_error": str(exc),
            "tool_retryable": False,
        }


def route_after_tool(state):
    if state["tool_error"] is None:
        return "success"

    if (
        state["tool_retryable"]
        and state["retry_count"] <= MAX_TOOL_RETRIES
    ):
        return "retry"

    return "failure"