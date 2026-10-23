"""Deterministic contracts for production Application failure routing."""

from app.application.graph import (
    finalize_application,
    route_after_decision,
    route_after_research,
    route_after_risk,
    route_after_valuation,
    _failure_update,
)


def test_failure_update_sets_one_canonical_failed_lifecycle_state():
    update = _failure_update(
        {"stage_errors": {"research": "earlier diagnostic"}},
        stage="valuation",
        message="Valuation input missing.",
        result_key="valuation",
        error_key="valuation_error",
    )

    assert update["execution_status"] == "failed"
    assert update["current_stage"] == "valuation"
    assert update["application_error"] == "valuation failed: Valuation input missing."
    assert update["stage_errors"] == {
        "research": "earlier diagnostic",
        "valuation": "Valuation input missing.",
    }
    assert update["valuation"] is None
    assert update["valuation_error"] == "Valuation input missing."


def test_failed_execution_cannot_route_downstream_even_if_result_is_present():
    # This intentionally inconsistent state simulates stale/merged result data.
    # The lifecycle status must take precedence over the presence of a result.
    state = {
        "execution_status": "failed",
        "application_error": "risk failed: provider unavailable",
        "risk_analysis": object(),
        "risk_error": "",
        "stage_errors": {},
    }
    assert route_after_risk(state) == "end"


def test_structured_error_detail_alone_fails_closed_for_routing_and_terminal_status():
    """结构化错误与生命周期字段不一致时，路由和终态仍必须失败关闭。"""
    state = {
        "execution_status": "running",
        "application_error": "",
        "stage_errors": {},
        "error_details": [{
            "stage": "risk",
            "code": "TRANSIENT_PROVIDER_FAILURE",
            "category": "transient_provider",
            "retryable": True,
            "handling_owner": "provider_retry_policy",
            "exception_type": "TransientProviderError",
            "message": "provider unavailable",
        }],
        "risk_analysis": object(),
        "risk_error": "",
    }

    assert route_after_risk(state) == "end"
    assert finalize_application(state)["execution_status"] == "failed"


def test_every_critical_stage_route_rejects_structured_errors_even_if_status_is_running():
    """各关键条件边都必须检查结构化错误，不能只依赖 execution_status。"""
    error_details = [{
        "stage": "upstream",
        "code": "STAGE_CONTRACT_VIOLATION",
        "category": "stage_contract",
        "retryable": False,
        "handling_owner": "application_stage_boundary",
        "exception_type": "StageContractError",
        "message": "invalid output",
    }]
    healthy_base = {
        "execution_status": "running",
        "application_error": "",
        "stage_errors": {},
        "error_details": error_details,
    }

    assert route_after_research({
        **healthy_base,
        "research_data_status": "complete",
        "company_research": object(),
        "financial_research": object(),
        "market_research": object(),
        "industry_macro_research": object(),
    }) == "end"
    assert route_after_valuation({
        **healthy_base, "valuation": object(), "valuation_error": ""
    }) == "end"
    assert route_after_risk({
        **healthy_base, "risk_analysis": object(), "risk_error": ""
    }) == "end"
    assert route_after_decision({
        **healthy_base, "investment_decision": object(), "decision_error": ""
    }) == "end"


def test_research_requires_running_status_and_no_research_error():
    healthy = {
        "execution_status": "running",
        "application_error": "",
        "stage_errors": {},
        "research_data_status": "complete",
        "company_research": object(),
        "financial_research": object(),
        "market_research": object(),
        "industry_macro_research": object(),
    }
    failed = {
        **healthy,
        "execution_status": "failed",
        "application_error": "research failed",
    }
    inconsistent = {
        **healthy,
        "stage_errors": {"research": "provider unavailable"},
    }

    assert route_after_research(healthy) == "continue"
    assert route_after_research(failed) == "end"
    assert route_after_research(inconsistent) == "end"


def test_valuation_risk_and_decision_routes_fail_closed_on_missing_contract_fields():
    healthy_base = {
        "execution_status": "running",
        "application_error": "",
        "stage_errors": {},
    }

    assert route_after_valuation({
        **healthy_base, "valuation": object(), "valuation_error": ""
    }) == "continue"
    assert route_after_valuation({
        **healthy_base, "valuation": object(), "valuation_error": "bad output"
    }) == "end"
    assert route_after_valuation({
        **healthy_base, "valuation": None, "valuation_error": ""
    }) == "end"

    assert route_after_risk({
        **healthy_base, "risk_analysis": object(), "risk_error": ""
    }) == "continue"
    assert route_after_risk({
        **healthy_base, "risk_analysis": None, "risk_error": ""
    }) == "end"

    assert route_after_decision({
        **healthy_base, "investment_decision": object(), "decision_error": ""
    }) == "continue"
    assert route_after_decision({
        **healthy_base, "investment_decision": object(), "decision_error": "invalid"
    }) == "end"


def test_final_output_exposes_terminal_execution_status():
    assert finalize_application({
        "current_stage": "completed",
        "execution_status": "completed",
    })["execution_status"] == "completed"
    assert finalize_application({
        "current_stage": "research",
        "application_error": "research failed",
    })["execution_status"] == "failed"
    assert finalize_application({
        "current_stage": "rejected",
        "approval_status": "rejected",
    })["execution_status"] == "rejected"


def test_production_graph_stops_at_the_first_failed_critical_stage(monkeypatch):
    """Exercise real graph edges with deterministic stage doubles, not real LLMs."""
    import app.application.graph as graph_module
    from app.application.graph import build_application_graph

    execution_order = []

    def approved(_state):
        return {
            "approval_status": "approved",
            "approval_reason": "test approval",
            "current_stage": "research",
            "execution_status": "running",
            "stage_errors": {},
            "application_error": "",
        }

    def healthy_stage(name, update):
        def run(_state):
            execution_order.append(name)
            return {
                **update,
                "current_stage": name,
                "execution_status": "running",
                "stage_errors": {},
                "application_error": "",
            }
        return run

    def failed_stage(name, result_key=None, error_key=None):
        def run(_state):
            execution_order.append(name)
            message = f"Injected {name} failure."
            update = {
                "current_stage": name,
                "execution_status": "failed",
                "stage_errors": {name: message},
                "application_error": f"{name} failed: {message}",
            }
            if result_key:
                update[result_key] = None
            if error_key:
                update[error_key] = message
            return update
        return run

    # Use valid-shaped placeholder outputs: this test concerns graph control flow,
    # not the domain validation already covered by the stage contract tests.
    stage_doubles = {
        "approval_gate": approved,
        "run_research_stage": healthy_stage("research", {
            "company_research": object(),
            "financial_research": object(),
            "market_research": object(),
            "industry_macro_research": object(),
            "research_data_status": "complete",
        }),
        "run_valuation_stage": healthy_stage("valuation", {
            "valuation": object(), "valuation_error": "",
        }),
        "run_risk_stage": healthy_stage("risk", {
            "risk_analysis": object(), "risk_error": "",
        }),
        "run_decision_stage": healthy_stage("investment_decision", {
            "investment_decision": object(), "decision_error": "",
        }),
        "run_report_stage": healthy_stage("report", {
            "report": object(), "report_markdown": "test report",
            "report_assembly_error": "", "report_generation_error": "",
            "report_merge_error": "", "report_rendering_error": "",
        }),
    }

    failure_cases = [
        ("research", "run_research_stage", failed_stage("research"), {"valuation", "risk", "investment_decision", "report"}),
        ("valuation", "run_valuation_stage", failed_stage("valuation", "valuation", "valuation_error"), {"risk", "investment_decision", "report"}),
        ("risk", "run_risk_stage", failed_stage("risk", "risk_analysis", "risk_error"), {"investment_decision", "report"}),
        ("investment_decision", "run_decision_stage", failed_stage("investment_decision", "investment_decision", "decision_error"), {"report"}),
        ("report", "run_report_stage", failed_stage("report", "report", "report_generation_error"), set()),
    ]

    for failure_name, function_name, failure_double, forbidden_downstream in failure_cases:
        execution_order.clear()
        for name, double in stage_doubles.items():
            monkeypatch.setattr(graph_module, name, double)
        monkeypatch.setattr(graph_module, function_name, failure_double)

        graph = build_application_graph(enable_default_memory=False)
        result = graph.invoke({"ticker": "AAPL", "user_query": "Test recovery routing"})

        assert result["execution_status"] == "failed", failure_name
        assert result["application_error"], failure_name
        assert failure_name in execution_order, failure_name
        assert not (forbidden_downstream & set(execution_order)), (
            failure_name,
            execution_order,
        )


def test_production_graph_normal_path_reaches_completed_terminal_state(monkeypatch):
    import app.application.graph as graph_module
    from app.application.graph import build_application_graph

    execution_order = []

    def approved(_state):
        return {
            "approval_status": "approved",
            "approval_reason": "test approval",
            "current_stage": "research",
            "execution_status": "running",
            "stage_errors": {},
            "application_error": "",
        }

    def stage(name, update):
        def run(_state):
            execution_order.append(name)
            return {
                **update,
                "current_stage": name,
                "execution_status": "running",
                "stage_errors": {},
                "application_error": "",
            }
        return run

    def report(_state):
        execution_order.append("report")
        return {
            "report": object(),
            "report_markdown": "# Test report",
            "report_assembly_error": "",
            "report_generation_error": "",
            "report_merge_error": "",
            "report_rendering_error": "",
            "current_stage": "completed",
            "execution_status": "completed",
            "stage_errors": {},
            "application_error": "",
        }

    monkeypatch.setattr(graph_module, "approval_gate", approved)
    monkeypatch.setattr(graph_module, "run_research_stage", stage("research", {
        "company_research": object(),
        "financial_research": object(),
        "market_research": object(),
        "industry_macro_research": object(),
        "research_data_status": "complete",
    }))
    monkeypatch.setattr(graph_module, "run_valuation_stage", stage("valuation", {
        "valuation": object(), "valuation_error": "",
    }))
    monkeypatch.setattr(graph_module, "run_risk_stage", stage("risk", {
        "risk_analysis": object(), "risk_error": "",
    }))
    monkeypatch.setattr(graph_module, "run_decision_stage", stage("investment_decision", {
        "investment_decision": object(), "decision_error": "",
    }))
    monkeypatch.setattr(graph_module, "run_report_stage", report)

    graph = build_application_graph(enable_default_memory=False)
    result = graph.invoke({"ticker": "AAPL", "user_query": "Test normal routing"})

    assert result["execution_status"] == "completed"
    assert result["application_error"] == ""
    assert execution_order == ["research", "valuation", "risk", "investment_decision", "report"]
