"""Tests for bounded subprocess execution around optional provider SDKs."""

import json
import time

import pytest

from app.providers.config import ProviderConfigurationError
from app.runtime.isolation import run_isolated_python_json


@pytest.mark.parametrize(
    ("module_name", "script_name"),
    [
        ("app.providers.akshare", "_AKSHARE_WORKER_SCRIPT"),
        ("app.providers.baostock", "_BAOSTOCK_WORKER_SCRIPT"),
        ("app.providers.sina_financials", "_SINA_FINANCIAL_WORKER_SCRIPT"),
    ],
)
def test_provider_worker_scripts_are_valid_python(module_name, script_name):
    import importlib

    module = importlib.import_module(module_name)
    compile(getattr(module, script_name), f"<{script_name}>", "exec")


def test_isolated_worker_returns_stdout_and_exit_code():
    code, stdout, _stderr = run_isolated_python_json(
        script='import json; print("__IRDA_RESULT__" + json.dumps({"ok": True}))',
        payload={"request_id": "test"},
        # Starting a fresh Python interpreter can be slow on Windows/PyCharm.
        # This is a success-path test, so keep the deadline generous; the
        # dedicated timeout test below verifies prompt termination separately.
        timeout_seconds=10.0,
        operation_name="test worker",
    )

    assert code == 0
    assert json.loads(stdout.strip().removeprefix("__IRDA_RESULT__")) == {"ok": True}


def test_isolated_worker_is_killed_when_timeout_expires():
    started = time.monotonic()
    with pytest.raises(TimeoutError, match="test worker"):
        run_isolated_python_json(
            script="import time; time.sleep(5)",
            payload={},
            timeout_seconds=0.25,
            operation_name="test worker",
        )
    assert time.monotonic() - started < 3.0


def test_akshare_production_call_uses_isolated_worker(monkeypatch):
    import app.providers.akshare as module
    from app.providers.akshare import AkShareClient

    captured = {}

    def fake_worker(**kwargs):
        captured.update(kwargs)
        return 0, '__IRDA_RESULT__[{"代码":"000001","最新价":11.2}]', ""

    monkeypatch.setattr(module, "run_isolated_python_json", fake_worker)
    monkeypatch.setattr(module, "provider_sdk_timeout_seconds", lambda: 7.0)

    records = AkShareClient().get_a_share_spot_records()

    assert records == [{"代码": "000001", "最新价": 11.2}]
    assert captured["timeout_seconds"] == 7.0
    assert captured["payload"]["method"] == "stock_zh_a_spot_em"


def test_akshare_worker_timeout_is_not_reclassified_as_transient(monkeypatch):
    import app.providers.akshare as module
    from app.providers.akshare import AkShareClient

    def timeout_worker(**kwargs):
        raise TimeoutError("SDK worker timed out")

    monkeypatch.setattr(module, "run_isolated_python_json", timeout_worker)
    with pytest.raises(TimeoutError, match="SDK worker timed out"):
        AkShareClient().get_a_share_spot_records()


def test_baostock_production_call_uses_isolated_worker(monkeypatch):
    import app.providers.baostock as module
    from app.providers.baostock import BaoStockClient

    monkeypatch.setattr(
        module,
        "run_isolated_python_json",
        lambda **kwargs: (
            0,
            '__IRDA_RESULT__' + json.dumps(
                {
                    "basic": [{"code": "sh.600000", "code_name": "浦发银行"}],
                    "industry": [{"code": "sh.600000", "industry": "银行"}],
                }
            ),
            "",
        ),
    )
    monkeypatch.setattr(module, "provider_sdk_timeout_seconds", lambda: 5.0)

    basic, industry = BaoStockClient().get_company_records("600000")

    assert basic[0]["code_name"] == "浦发银行"
    assert industry[0]["industry"] == "银行"


def test_baostock_worker_timeout_is_not_reclassified_as_transient(monkeypatch):
    import app.providers.baostock as module
    from app.providers.baostock import BaoStockClient

    monkeypatch.setattr(
        module,
        "run_isolated_python_json",
        lambda **kwargs: (_ for _ in ()).throw(TimeoutError("BaoStock timed out")),
    )
    with pytest.raises(TimeoutError, match="BaoStock timed out"):
        BaoStockClient().get_company_records("600000")


def test_sina_financial_statement_uses_isolated_worker(monkeypatch):
    import app.providers.sina_financials as module
    from app.providers.sina_financials import SinaFinancialStatementClient

    monkeypatch.setattr(
        module,
        "run_isolated_python_json",
        lambda **kwargs: (
            0,
            '__IRDA_RESULT__' + json.dumps([{"报告日": "20251231", "营业总收入": 100, "净利润": 10}]),
            "",
        ),
    )
    monkeypatch.setattr(module, "provider_sdk_timeout_seconds", lambda: 6.0)

    rows = SinaFinancialStatementClient().get_income_statement_records("600000")

    assert rows == [{"报告日": "20251231", "营业总收入": 100, "净利润": 10}]


def test_sina_financial_statement_missing_akshare_is_configuration_error(monkeypatch):
    import app.providers.sina_financials as module
    from app.providers.sina_financials import SinaFinancialStatementClient

    monkeypatch.setattr(
        module,
        "run_isolated_python_json",
        lambda **kwargs: (
            2,
            '__IRDA_ERROR__' + json.dumps(
                {"type": "ModuleNotFoundError", "module": "akshare", "message": "missing"}
            ),
            "",
        ),
    )
    with pytest.raises(ProviderConfigurationError, match="akshare"):
        SinaFinancialStatementClient().get_income_statement_records("600000")

