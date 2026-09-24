from app.graph.nodes.tool_node import get_stock_price_node


def test_get_stock_price_result_updates_graph_state_aapl():
    state = {
        "ticker": "AAPL",
    }

    result = get_stock_price_node(state)

    assert result["current_price"] == 200.0
    assert result["tool_error"] is None


def test_get_stock_price_result_updates_graph_state_msft():
    state = {
        "ticker": "MSFT",
    }

    result = get_stock_price_node(state)

    assert result["current_price"] == 450.0
    assert result["tool_error"] is None


def test_get_stock_price_tool_failure():
    state = {
        "ticker": "INVALID",
    }

    result = get_stock_price_node(state)

    assert "tool_error" in result
    assert result["tool_error"] is not None
    assert "INVALID" in result["tool_error"]


def test_retryable_tool_failure():
    state = {
        "ticker": "TEMP_ERROR",
        "tool_retry_count": 0,
    }

    result = get_stock_price_node(state)

    assert result["tool_error"] is not None
    assert result["tool_retryable"] is True
    assert result["tool_retry_count"] == 1


def test_invalid_ticker_is_not_retryable():
    state = {
        "ticker": "INVALID",
        "tool_retry_count": 0,
    }

    result = get_stock_price_node(state)

    assert result["tool_error"] is not None
    assert result["tool_retryable"] is False
    assert "INVALID" in result["tool_error"]