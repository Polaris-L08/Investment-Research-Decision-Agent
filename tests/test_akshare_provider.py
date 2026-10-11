import pytest

from app.providers.akshare import (
    AkShareClient,
    AkShareCompanyInfoProvider,
    AkShareIncomeStatementProvider,
    AkShareStockPriceProvider,
)
from app.providers.config import ProviderConfigurationError, ProviderSettings
from app.providers.exceptions import TransientProviderError
from app.providers.factory import create_provider_bundle


class FakeFrame:
    def __init__(self, rows):
        self._rows = rows
        self.empty = not rows
        self.columns = list(rows[0]) if rows else []

    def to_dict(self, orient="records"):
        assert orient == "records"
        return list(self._rows)


class FakeAkShare:
    def __init__(self):
        self.spot_calls = 0
        self.info_calls = []
        self.statement_calls = []

    def stock_zh_a_spot_em(self):
        self.spot_calls += 1
        return FakeFrame([
            {"代码": "000001", "名称": "平安银行", "最新价": 11.23},
            {"代码": "600000", "名称": "浦发银行", "最新价": 10.12},
        ])

    def stock_individual_info_em(self, symbol):
        self.info_calls.append(symbol)
        return FakeFrame([
            {"item": "股票代码", "value": symbol},
            {"item": "股票简称", "value": "平安银行"},
            {"item": "总市值", "value": "216000000000"},
            {"item": "行业", "value": "银行"},
            {"item": "上市时间", "value": "1991-04-03"},
        ])

    def stock_profit_sheet_by_report_em(self, symbol):
        self.statement_calls.append(symbol)
        return FakeFrame([
            {"报告日期": "2025-09-30", "营业总收入": 120000000, "净利润": 32000000},
            {"报告日期": "2024-12-31", "营业总收入": 150000000, "净利润": 40000000},
            {"报告日期": "2025-12-31", "营业总收入": 160000000, "净利润": 45000000},
        ])


def test_akshare_quote_normalizes_a_share_code_and_caches_snapshot():
    ak = FakeAkShare()
    client = AkShareClient(ak_module=ak, clock=lambda: 100.0)
    provider = AkShareStockPriceProvider(client)

    result = provider.get_stock_price(" SZ000001 ")
    second = provider.get_stock_price("000001")

    assert result["ticker"] == "000001"
    assert result["price"] == 11.23
    assert result["currency"] == "CNY"
    assert result["latest_trading_day"] is None
    assert result["source"].startswith("AKShare stock_zh_a_spot_em")
    assert second["price"] == 11.23
    assert ak.spot_calls == 1


def test_akshare_company_info_normalizes_item_value_table():
    provider = AkShareCompanyInfoProvider(AkShareClient(ak_module=FakeAkShare()))
    result = provider.get_company_info("000001")

    assert result["ticker"] == "000001"
    assert result["company_name"] == "平安银行"
    assert result["sector"] == "银行"
    assert result["market_cap"] == 216000000000.0
    assert result["currency"] == "CNY"
    assert result["source"].startswith("AKShare stock_individual_info_em")


def test_akshare_financials_choose_latest_annual_report_and_share_cache():
    ak = FakeAkShare()
    provider = AkShareIncomeStatementProvider(AkShareClient(ak_module=ak))

    assert provider.get_revenue("000001") == 160000000.0
    assert provider.get_net_income("SZ000001") == 45000000.0
    result = provider.get_latest_annual_report("000001")

    assert result["fiscal_date_ending"] == "2025-12-31"
    assert result["period"] == "annual"
    assert result["unit"] == "CNY"
    assert len(ak.statement_calls) == 1


def test_akshare_financials_reject_missing_annual_period():
    class NoAnnual(FakeAkShare):
        def stock_profit_sheet_by_report_em(self, symbol):
            return FakeFrame([
                {"报告日期": "2025-09-30", "营业总收入": 12, "净利润": 3}
            ])

    provider = AkShareIncomeStatementProvider(AkShareClient(ak_module=NoAnnual()))
    with pytest.raises(ValueError, match="no annual"):
        provider.get_revenue("000001")


def test_akshare_rejects_invalid_ticker_before_network_call():
    ak = FakeAkShare()
    provider = AkShareStockPriceProvider(AkShareClient(ak_module=ak))
    with pytest.raises(ValueError, match="six-digit"):
        provider.get_stock_price("AAPL")
    assert ak.spot_calls == 0


def test_akshare_empty_snapshot_is_transient_error():
    class EmptyAk:
        def stock_zh_a_spot_em(self):
            return FakeFrame([])

    provider = AkShareStockPriceProvider(AkShareClient(ak_module=EmptyAk()))
    with pytest.raises(TransientProviderError, match="empty A-share spot snapshot"):
        provider.get_stock_price("000001")


def test_factory_can_select_akshare_without_alpha_vantage_key(monkeypatch):
    from app.providers.akshare import (
        AkShareCompanyInfoProvider,
        AkShareIncomeStatementProvider,
        AkShareStockPriceProvider,
    )

    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    settings = ProviderSettings(
        app_env="development", mode="real", real_provider_source="akshare"
    )
    bundle = create_provider_bundle(settings)

    assert bundle.mode == "real-partial"
    assert isinstance(bundle.stock_price, AkShareStockPriceProvider)
    assert isinstance(bundle.company_info, AkShareCompanyInfoProvider)
    assert isinstance(bundle.revenue, AkShareIncomeStatementProvider)
    assert bundle.net_income is bundle.revenue


def test_provider_settings_reject_unknown_real_source():
    with pytest.raises(ProviderConfigurationError, match="REAL_PROVIDER_SOURCE"):
        ProviderSettings(app_env="development", mode="real", real_provider_source="unknown")
