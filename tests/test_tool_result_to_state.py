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