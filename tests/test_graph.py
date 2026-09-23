from app.graph.graph import graph


def test_graph_separates_input_internal_state_and_output() -> None:
    result = graph.invoke(
        {
            "user_query": "Research Apple as a long-term investment",
            "ticker": "AAPL",
        }
    )

    assert result == {
        "ticker": "AAPL",
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "current_price": 0.0,
        "target_price": 0.0,
        "investment_thesis": "",
    }