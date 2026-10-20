"""Deterministic tests for the shared LLM client's bounded retry policy."""

import json

import httpx
import pytest
from openai import APIStatusError

from app.llm import client as llm_client


SUCCESS_BODY = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "created": 1_700_000_000,
    "model": "test-model",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "ok"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}


def _response(request: httpx.Request, status_code: int, body: dict, **headers: str):
    return httpx.Response(
        status_code,
        request=request,
        headers={"content-type": "application/json", **headers},
        content=json.dumps(body).encode("utf-8"),
    )


def _set_llm_env(monkeypatch):
    monkeypatch.delenv("LLM_REQUEST_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://llm.test/v1")


def test_retry_limit_is_bounded_and_counts_retries_after_initial_attempt():
    assert llm_client.LLM_MAX_RETRIES == 2
    assert llm_client.LLM_MAX_RETRIES + 1 == 3


def test_build_llm_configures_retry_limit(monkeypatch):
    _set_llm_env(monkeypatch)
    captured = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(llm_client, "ChatOpenAI", FakeChatOpenAI)

    result = llm_client.build_llm()

    assert isinstance(result, FakeChatOpenAI)
    assert captured["max_retries"] == 2
    assert captured["timeout"] == 30.0
    assert captured["temperature"] == 0
    assert captured["model"] == "test-model"
    assert captured["api_key"] == "test-key"
    assert captured["base_url"] == "https://llm.test/v1"


def test_transient_server_error_retries_then_succeeds(monkeypatch):
    _set_llm_env(monkeypatch)
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            # The SDK honors this header, keeping the test deterministic/fast.
            return _response(
                request,
                503,
                {"error": {"message": "temporary outage", "type": "server_error"}},
                **{"retry-after-ms": "1", "x-should-retry": "true"},
            )
        return _response(request, 200, SUCCESS_BODY)

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        model = llm_client.build_llm(http_client=transport)
        result = model.invoke("Say ok")

    assert result.content == "ok"
    assert attempts == 2


def test_retryable_failure_exhausts_at_initial_attempt_plus_max_retries(monkeypatch):
    _set_llm_env(monkeypatch)
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return _response(
            request,
            503,
            {"error": {"message": "still unavailable", "type": "server_error"}},
            **{"retry-after-ms": "1", "x-should-retry": "true"},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        model = llm_client.build_llm(http_client=transport)
        with pytest.raises(APIStatusError):
            model.invoke("Say ok")

    assert attempts == llm_client.LLM_MAX_RETRIES + 1


def test_non_retryable_client_error_is_not_retried(monkeypatch):
    _set_llm_env(monkeypatch)
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return _response(
            request,
            400,
            {"error": {"message": "invalid request", "type": "invalid_request_error"}},
            **{"x-should-retry": "false"},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        model = llm_client.build_llm(http_client=transport)
        with pytest.raises(APIStatusError):
            model.invoke("Say ok")

    assert attempts == 1


def test_build_llm_uses_positive_timeout_override(monkeypatch):
    _set_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT_SECONDS", "12.5")
    captured = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(llm_client, "ChatOpenAI", FakeChatOpenAI)
    llm_client.build_llm()

    assert captured["timeout"] == 12.5
    assert captured["max_retries"] == 2


@pytest.mark.parametrize("raw_timeout", ["0", "-1", "nan", "inf", "not-a-number"])
def test_build_llm_rejects_invalid_timeout_configuration(monkeypatch, raw_timeout):
    _set_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT_SECONDS", raw_timeout)

    with pytest.raises(ValueError, match="LLM_REQUEST_TIMEOUT_SECONDS"):
        llm_client.build_llm()
