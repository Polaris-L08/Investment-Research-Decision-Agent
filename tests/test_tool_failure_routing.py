from app.graph.nodes.tool_node import route_after_tool


def test_tool_success_routes_to_success():
    state = {
        "tool_error": None,
        "tool_retryable": False,
        "retry_count": 0,
    }

    assert route_after_tool(state) == "success"


def test_retryable_tool_failure_routes_to_retry():
    state = {
        "tool_error": "Temporary error",
        "tool_retryable": True,
        "retry_count": 1,
    }

    assert route_after_tool(state) == "retry"


def test_retryable_tool_failure_stops_after_max_retries():
    state = {
        "tool_error": "Temporary error",
        "tool_retryable": True,
        "retry_count": 3,
    }

    assert route_after_tool(state) == "failure"


def test_non_retryable_tool_failure_routes_to_failure():
    state = {
        "tool_error": "Invalid ticker",
        "tool_retryable": False,
        "retry_count": 0,
    }

    assert route_after_tool(state) == "failure"