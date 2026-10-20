"""Timeout contracts for HTTP adapters and optional provider SDKs."""

import pytest

from app.providers.alpha_vantage import AlphaVantageClient
from app.providers.exceptions import TransientProviderError
from app.providers.sina import SinaFinanceClient
from app.runtime.isolation import provider_sdk_timeout_seconds


@pytest.mark.parametrize(
    ("client_factory", "invoke"),
    [
        (
            lambda opener: AlphaVantageClient(
                api_key="test-key", opener=opener, min_request_interval=0
            ),
            lambda client: client.get_json("GLOBAL_QUOTE", "IBM"),
        ),
        (
            lambda opener: SinaFinanceClient(opener=opener),
            lambda client: client.get_quote_text("600000"),
        ),
    ],
)
def test_http_providers_pass_finite_timeout_to_opener(client_factory, invoke):
    captured = {}

    def opener(request, *, timeout):
        captured["timeout"] = timeout
        raise TimeoutError("simulated request timeout")

    with pytest.raises(TransientProviderError):
        invoke(client_factory(opener))

    assert captured["timeout"] == 10.0


def test_provider_sdk_timeout_defaults_to_30_seconds(monkeypatch):
    monkeypatch.delenv("PROVIDER_SDK_TIMEOUT_SECONDS", raising=False)
    assert provider_sdk_timeout_seconds() == 30.0


def test_provider_sdk_timeout_accepts_positive_override(monkeypatch):
    monkeypatch.setenv("PROVIDER_SDK_TIMEOUT_SECONDS", "4.25")
    assert provider_sdk_timeout_seconds() == 4.25


@pytest.mark.parametrize("raw", ["0", "-1", "nan", "inf", "not-a-number"])
def test_provider_sdk_timeout_rejects_invalid_configuration(monkeypatch, raw):
    monkeypatch.setenv("PROVIDER_SDK_TIMEOUT_SECONDS", raw)
    with pytest.raises(ValueError, match="PROVIDER_SDK_TIMEOUT_SECONDS"):
        provider_sdk_timeout_seconds()
