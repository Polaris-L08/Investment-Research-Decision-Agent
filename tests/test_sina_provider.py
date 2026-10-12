import io

import pytest

from app.providers.config import ProviderConfigurationError, ProviderSettings
from app.providers.exceptions import TransientProviderError
from app.providers.factory import create_provider_bundle
from app.providers.sina import SinaFinanceClient, SinaStockPriceProvider
from app.providers.unavailable import UnavailableRealProvider


class FakeResponse:
    status = 200

    def __init__(self, body: bytes):
        self._body = body
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


def fake_opener(body: bytes, seen=None):
    def opener(request, timeout):
        if seen is not None:
            seen["url"] = request.full_url
            seen["headers"] = dict(request.header_items())
            seen["timeout"] = timeout
        return FakeResponse(body)
    return opener


def quote_body(symbol="sh600000", payload=None):
    if payload is None:
        fields = ["浦发银行", "9.700", "9.700", "9.540", "9.740", "9.540", "9.540", "9.550", "94795849", "915309833.000"]
        # Sina's fixed quote schema includes five bid levels, five ask levels,
        # then trading date, trading time, and a trailing status field.
        fields += ["0", "9.540"] * 10
        fields += ["2026-10-09", "15:34:59", "00"]
        payload = ",".join(fields)
    return f'var hq_str_{symbol}="{payload}";'.encode("gb18030")


def test_sina_quote_parses_price_date_volume_and_turnover():
    provider = SinaStockPriceProvider(
        SinaFinanceClient(opener=fake_opener(quote_body()))
    )
    result = provider.get_stock_price("SH600000")

    assert result["ticker"] == "600000"
    assert result["company_name"] == "浦发银行"
    assert result["price"] == 9.54
    assert result["latest_trading_day"] == "2026-10-09"
    assert result["source_timestamp"] == "2026-10-09 15:34:59"
    assert result["volume_shares"] == 94795849.0
    assert result["turnover_cny"] == 915309833.0
    assert result["currency"] == "CNY"
    assert result["source"] == "Sina Finance hq.sinajs.cn"


def test_sina_maps_exchange_prefix_and_sets_request_headers():
    seen = {}
    provider = SinaStockPriceProvider(
        SinaFinanceClient(opener=fake_opener(quote_body("sz000001"), seen))
    )
    result = provider.get_stock_price("SZ000001")

    assert result["ticker"] == "000001"
    assert seen["url"].endswith("list=sz000001")
    headers = {key.lower(): value for key, value in seen["headers"].items()}
    assert headers["user-agent"]
    assert headers["referer"] == "https://finance.sina.com.cn/"


def test_sina_rejects_invalid_ticker_before_request():
    provider = SinaStockPriceProvider(SinaFinanceClient(opener=fake_opener(quote_body())))
    with pytest.raises(ValueError, match="six-digit"):
        provider.get_stock_price("AAPL")


def test_sina_rejects_empty_or_mismatched_response():
    empty = SinaStockPriceProvider(
        SinaFinanceClient(opener=fake_opener(quote_body(payload="")))
    )
    with pytest.raises(ValueError, match="No Sina Finance quote data"):
        empty.get_stock_price("600000")

    mismatch = SinaStockPriceProvider(
        SinaFinanceClient(opener=fake_opener(quote_body("sz000001")))
    )
    with pytest.raises(TransientProviderError, match="returned quote symbol"):
        mismatch.get_stock_price("600000")


def test_sina_rejects_non_positive_price():
    body = quote_body(payload=",".join(["浦发银行", "0", "0", "0"] + ["0"] * 29))
    provider = SinaStockPriceProvider(SinaFinanceClient(opener=fake_opener(body)))
    with pytest.raises(TransientProviderError, match="non-positive"):
        provider.get_stock_price("600000")


def test_factory_selects_sina_quote_and_fails_closed_for_fundamentals(monkeypatch):
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    settings = ProviderSettings(
        app_env="development", mode="real", real_provider_source="sina"
    )
    bundle = create_provider_bundle(settings)

    assert bundle.mode == "real-partial"
    assert isinstance(bundle.stock_price, SinaStockPriceProvider)
    assert isinstance(bundle.company_info, UnavailableRealProvider)
    assert isinstance(bundle.revenue, UnavailableRealProvider)
    assert bundle.net_income is bundle.revenue
    with pytest.raises(ProviderConfigurationError, match="No Mock fallback"):
        bundle.company_info.get_company_info("600000")
    with pytest.raises(ProviderConfigurationError, match="No Mock fallback"):
        bundle.revenue.get_revenue("600000")


def test_provider_settings_accept_sina_and_reject_unknown_sources():
    assert ProviderSettings(
        app_env="development", mode="real", real_provider_source="sina"
    ).real_provider_source == "sina"
    with pytest.raises(ProviderConfigurationError, match="alpha_vantage, akshare, sina"):
        ProviderSettings(app_env="development", mode="real", real_provider_source="unknown")
