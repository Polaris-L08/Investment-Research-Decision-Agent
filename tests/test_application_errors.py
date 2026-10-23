"""Tests for the Application error taxonomy introduced in Phase 12 Lesson 1."""
from app.application.contracts import StageContractError
from app.application.errors import classify_exception, make_error_detail
from app.providers.config import ProviderConfigurationError
from app.providers.exceptions import TransientProviderError


def test_transient_provider_error_is_classified_as_retry_candidate():
    result = classify_exception(TransientProviderError("provider unavailable"))

    assert result == {
        "code": "TRANSIENT_PROVIDER_FAILURE",
        "category": "transient_provider",
        "retryable": True,
        "handling_owner": "provider_retry_policy",
    }


def test_provider_configuration_error_is_not_retryable():
    result = classify_exception(ProviderConfigurationError("missing API key"))

    assert result["category"] == "provider_configuration"
    assert result["retryable"] is False
    assert result["handling_owner"] == "provider_configuration_boundary"


def test_stage_contract_error_is_not_retryable():
    result = classify_exception(StageContractError("invalid stage output"))

    assert result["code"] == "STAGE_CONTRACT_VIOLATION"
    assert result["retryable"] is False


def test_timeout_retryability_is_deferred_to_policy():
    result = classify_exception(TimeoutError("request timed out"))

    assert result["category"] == "timeout"
    assert result["retryable"] is None


def test_unknown_exception_is_not_assumed_retryable():
    result = classify_exception(RuntimeError("unexpected bug"))

    assert result["category"] == "unexpected"
    assert result["retryable"] is None


def test_error_detail_preserves_exception_type_and_message():
    detail = make_error_detail(
        stage="research",
        message="message passed by caller",
        exc=TransientProviderError("original provider detail"),
    )

    assert detail["stage"] == "research"
    assert detail["exception_type"] == "TransientProviderError"
    assert detail["message"] == "original provider detail"
    assert detail["retryable"] is True


def test_child_stage_string_does_not_falsely_claim_root_exception_or_retryability():
    detail = make_error_detail(
        stage="research",
        message="Research planner invocation failed",
    )

    assert detail["code"] == "STAGE_REPORTED_FAILURE"
    assert detail["exception_type"] == ""
    assert detail["retryable"] is None


def test_application_stage_failure_keeps_structured_exception_diagnostics(monkeypatch):
    import app.application.graph as application_graph_module
    class FailingResearchGraph:
        def invoke(self, payload):
            raise TransientProviderError("temporary upstream outage")

    monkeypatch.setattr(
        application_graph_module, "research_supervisor_graph", FailingResearchGraph()
    )
    result = application_graph_module.run_research_stage(
        {"ticker": "AAPL", "user_query": "research Apple", "error_details": []}
    )

    assert result["current_stage"] == "research"
    assert result["application_error"]
    assert result["error_details"][-1]["exception_type"] == "TransientProviderError"
    assert result["error_details"][-1]["category"] == "transient_provider"
    assert result["error_details"][-1]["retryable"] is True


def test_invalid_public_input_is_recorded_as_non_retryable_validation_error():
    from app.application.graph import validate_application_input

    result = validate_application_input({"ticker": " ", "user_query": "research"})

    detail = result["error_details"][-1]
    assert result["execution_status"] == "failed"
    assert detail["code"] == "INVALID_TICKER"
    assert detail["category"] == "input_validation"
    assert detail["retryable"] is False
    assert detail["handling_owner"] == "application_input_boundary"


def test_application_stage_does_not_convert_cancellation_into_failure_state(monkeypatch):
    import asyncio
    import app.application.graph as application_graph_module

    class CancelledResearchGraph:
        def invoke(self, payload):
            raise asyncio.CancelledError()

    monkeypatch.setattr(
        application_graph_module, "research_supervisor_graph", CancelledResearchGraph()
    )

    import pytest

    with pytest.raises(asyncio.CancelledError):
        application_graph_module.run_research_stage(
            {"ticker": "AAPL", "user_query": "research Apple", "error_details": []}
        )
