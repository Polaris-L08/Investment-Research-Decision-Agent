"""Contract checks for the top-level graph's long-term-memory integration."""
from app.application.graph import build_application_graph


def test_application_graph_contains_memory_read_and_capture_nodes():
    graph = build_application_graph(enable_default_memory=False)
    node_names = set(graph.get_graph().nodes)
    assert "load_memory_context" in node_names
    assert "capture_memory" in node_names
    assert "research" in node_names
    assert "report" in node_names
    assert "finalize" in node_names


def test_memory_nodes_are_on_the_main_workflow_path():
    graph = build_application_graph(enable_default_memory=False)
    edges = {(edge.source, edge.target) for edge in graph.get_graph().edges}
    assert ("approval_gate", "load_memory_context") in edges
    assert ("load_memory_context", "research") in edges
    assert ("report", "capture_memory") in edges
    assert ("capture_memory", "finalize") in edges


def test_finalizer_does_not_expose_memory_context_text():
    from app.application.graph import finalize_application

    result = finalize_application({
        "ticker": "ACME",
        "memory_context": "private prior memory content",
        "memory_context_error": "",
        "memory_capture_decision": "skipped",
    })
    assert "memory_context" not in result
    assert "private prior memory content" not in repr(result)
    assert result["memory_capture_decision"] == "skipped"


def test_only_approved_runs_enter_memory_read_path():
    from app.application.graph import route_after_approval

    assert route_after_approval({
        "approval_status": "approved",
        "execution_status": "running",
        "application_error": "",
    }) == "continue"
    assert route_after_approval({
        "approval_status": "approved",
        "execution_status": "failed",
        "application_error": "research failed",
    }) == "end"
    assert route_after_approval({"approval_status": "rejected"}) == "end"
    assert route_after_approval({"approval_status": "invalid"}) == "end"
