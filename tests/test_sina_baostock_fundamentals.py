from __future__ import annotations

import pytest

from app.providers.baostock import BaoStockClient, BaoStockCompanyInfoProvider
from app.providers.config import ProviderConfigurationError, ProviderSettings
from app.providers.exceptions import TransientProviderError
from app.providers.factory import create_provider_bundle
from app.providers.sina import SinaStockPriceProvider
from app.providers.sina_financials import SinaFinancialStatementClient, SinaIncomeStatementProvider
from app.providers.sina import SinaStockPriceProvider


class FakeFrame:
    def __init__(self, rows):
        self.rows = rows
        self.empty = not rows

    def to_dict(self, orient="records"):
        assert orient == "records"
        return list(self.rows)


class FakeBaoStockClient:
    def get_company_records(self, ticker):
        code = "sh.600000" if ticker == "600000" else "sz.000001"
        return (
            [{"code": code, "code_name": "浦发银行", "ipoDate": "1999-11-10", "status": "1"}],
            [{"code": code, "industry": "银行", "industryClassification": "金融"}],
        )


class FakeSinaAk:
    def __init__(self, frame):
        self.frame = frame
        self.calls = []

    def stock_financial_report_sina(self, stock, symbol):
        self.calls.append((stock, symbol))
        return self.frame


def test_baostock_company_profile_maps_basic_and_industry_fields():
    provider = BaoStockCompanyInfoProvider(FakeBaoStockClient())
    result = provider.get_company_info("SH600000")

    assert result["ticker"] == "600000"
    assert result["company_name"] == "浦发银行"
    assert result["sector"] == "银行"
    assert result["industry_classification"] == "金融"
    assert result["exchange"] == "SSE"
    assert result["listing_date"] == "1999-11-10"
    assert result["source"].startswith("BaoStock")


def test_baostock_company_profile_rejects_beijing_market_until_validated():
    provider = BaoStockCompanyInfoProvider(FakeBaoStockClient())
    with pytest.raises(ValueError, match="Shanghai/Shenzhen"):
        provider.get_company_info("830799")


def test_sina_financials_choose_latest_annual_total_operating_revenue_and_net_income():
    ak = FakeSinaAk(FakeFrame([
        {"报告日": "20250930", "营业总收入": 120000000.0, "净利润": 31000000.0},
        {"报告日": "20241231", "营业总收入": 150000000.0, "净利润": 40000000.0},
        {"报告日": "20251231", "营业总收入": 160000000.0, "净利润": 45000000.0},
    ]))
    provider = SinaIncomeStatementProvider(SinaFinancialStatementClient(ak_module=ak))

    assert provider.get_revenue("600000") == 160000000.0
    assert provider.get_net_income("SH600000") == 45000000.0
    report = provider.get_latest_annual_report("600000")
    assert report["fiscal_date_ending"] == "2025-12-31"
    assert report["revenue_metric"] == "total_operating_revenue"
    assert report["net_income_metric"] == "净利润"
    assert report["unit"] == "CNY"
    assert report["source"].startswith("Sina Finance")
    assert ak.calls == [("sh600000", "利润表")]


def test_sina_financials_do_not_substitute_quarterly_data_for_annual_data():
    ak = FakeSinaAk(FakeFrame([
        {"报告日": "20250930", "营业总收入": 120000000.0, "净利润": 31000000.0},
    ]))
    provider = SinaIncomeStatementProvider(SinaFinancialStatementClient(ak_module=ak))
    with pytest.raises(ValueError, match="no annual"):
        provider.get_revenue("600000")


def test_sina_financials_reject_missing_required_metric():
    ak = FakeSinaAk(FakeFrame([
        {"报告日": "20251231", "营业总收入": 120000000.0},
    ]))
    provider = SinaIncomeStatementProvider(SinaFinancialStatementClient(ak_module=ak))
    with pytest.raises(ValueError, match="missing a required field"):
        provider.get_net_income("600000")


def test_sina_financials_reject_invalid_ticker_before_call():
    ak = FakeSinaAk(FakeFrame([]))
    provider = SinaIncomeStatementProvider(SinaFinancialStatementClient(ak_module=ak))
    with pytest.raises(ValueError, match="six-digit"):
        provider.get_revenue("AAPL")
    assert ak.calls == []


def test_factory_selects_explicit_sina_baostock_composite(monkeypatch):
    from app.providers.baostock import BaoStockCompanyInfoProvider
    from app.providers.sina_financials import SinaIncomeStatementProvider

    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    settings = ProviderSettings(
        app_env="development", mode="real", real_provider_source="sina_baostock"
    )
    bundle = create_provider_bundle(settings)

    assert bundle.mode == "real-partial"
    assert isinstance(bundle.stock_price, SinaStockPriceProvider)
    assert isinstance(bundle.company_info, BaoStockCompanyInfoProvider)
    assert isinstance(bundle.revenue, SinaIncomeStatementProvider)
    assert bundle.net_income is bundle.revenue


def test_provider_settings_accepts_sina_baostock():
    assert ProviderSettings(
        app_env="development", mode="real", real_provider_source="sina_baostock"
    ).real_provider_source == "sina_baostock"


def test_baostock_client_checks_login_and_logs_out():
    class LoginResult:
        error_code = "0"
        error_msg = "success"

    class QueryResult:
        error_code = "0"
        error_msg = "success"

        def __init__(self, rows, fields):
            self.rows = list(rows)
            self.fields = fields

        def next(self):
            return bool(self.rows)

        def get_row_data(self):
            return self.rows.pop(0)

    class FakeBs:
        def __init__(self):
            self.logged_out = False
            self.codes = []

        def login(self):
            return LoginResult()

        def query_stock_basic(self, code):
            self.codes.append(("basic", code))
            return QueryResult([[code, "浦发银行", "1999-11-10", "1"]], ["code", "code_name", "ipoDate", "status"])

        def query_stock_industry(self, code):
            self.codes.append(("industry", code))
            return QueryResult([[code, "浦发银行", "银行", "金融"]], ["code", "code_name", "industry", "industryClassification"])

        def logout(self):
            self.logged_out = True

    fake_bs = FakeBs()
    client = BaoStockClient(baostock_module=fake_bs)
    basic, industry = client.get_company_records("600000")

    assert basic[0]["code_name"] == "浦发银行"
    assert industry[0]["industry"] == "银行"
    assert fake_bs.logged_out is True
    assert fake_bs.codes == [("basic", "sh.600000"), ("industry", "sh.600000")]


def test_baostock_client_classifies_query_error_as_transient():
    class LoginResult:
        error_code = "0"
        error_msg = "success"

    class ErrorResult:
        error_code = "10001"
        error_msg = "upstream unavailable"
        fields = []

    class FakeBs:
        def login(self):
            return LoginResult()

        def query_stock_basic(self, code):
            return ErrorResult()

        def logout(self):
            pass

    with pytest.raises(TransientProviderError, match="upstream unavailable"):
        BaoStockClient(baostock_module=FakeBs()).get_company_records("600000")
