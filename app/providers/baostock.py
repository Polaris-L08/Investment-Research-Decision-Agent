"""BaoStock company metadata adapter for the explicit Sina+BaoStock bundle.

BaoStock is used here only for A-share company metadata. Quotes and income
statements are provided by the separately identified Sina endpoints.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.providers.config import ProviderConfigurationError
from app.providers.exceptions import TransientProviderError
from app.providers.financial import CompanyInfoProvider
from app.runtime.isolation import provider_sdk_timeout_seconds, run_isolated_python_json


_BAOSTOCK_WORKER_SCRIPT = r'''import contextlib, importlib, io, json, sys
payload = json.load(sys.stdin)
try:
    with contextlib.redirect_stdout(io.StringIO()):
        bs = importlib.import_module("baostock")
        login_result = bs.login()
        if str(getattr(login_result, "error_code", "1")) != "0":
            raise RuntimeError("BaoStock login failed: " + str(getattr(login_result, "error_msg", "unknown provider error")))
        try:
            def collect(result, label):
                error_code = str(getattr(result, "error_code", "0"))
                if error_code != "0":
                    raise RuntimeError("BaoStock " + label + " query failed: " + str(getattr(result, "error_msg", "unknown provider error")))
                fields = list(getattr(result, "fields", []) or [])
                rows = []
                while result.next():
                    rows.append(dict(zip(fields, result.get_row_data())))
                return rows
            basic = collect(bs.query_stock_basic(code=payload["code"]), "stock basic")
            industry = collect(bs.query_stock_industry(code=payload["code"]), "stock industry")
        finally:
            try:
                bs.logout()
            except Exception:
                pass
    print("__IRDA_RESULT__" + json.dumps({"basic": basic, "industry": industry}, ensure_ascii=False, default=str))
except Exception as exc:
    print("__IRDA_ERROR__" + json.dumps({"type": type(exc).__name__, "message": str(exc), "module": getattr(exc, "name", None)}, ensure_ascii=False))
    sys.exit(2)
'''


class BaoStockClient:
    """BaoStock client with a bounded worker for production SDK sessions.

    An injected module remains in-process for deterministic unit tests.
    """

    def __init__(self, baostock_module: Any | None = None) -> None:
        self._baostock_module = baostock_module
        self._injected_baostock_module = baostock_module is not None

    def get_company_records(self, ticker: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        code = _baostock_code(ticker)
        if not self._injected_baostock_module:
            returncode, stdout, _stderr = run_isolated_python_json(
                script=_BAOSTOCK_WORKER_SCRIPT,
                payload={"code": code},
                timeout_seconds=provider_sdk_timeout_seconds(),
                operation_name="BaoStock company metadata query",
            )
            marker = next(
                (line for line in reversed(stdout.splitlines()) if line.startswith("__IRDA_")),
                None,
            )
            if marker is None:
                raise TransientProviderError(
                    "BaoStock worker failed without a result marker "
                    f"(exit={returncode})."
                )
            if marker.startswith("__IRDA_ERROR__"):
                detail = json.loads(marker.removeprefix("__IRDA_ERROR__"))
                if detail.get("type") == "ModuleNotFoundError" and detail.get("module") == "baostock":
                    raise ProviderConfigurationError(
                        "REAL_PROVIDER_SOURCE=sina_baostock requires the optional 'baostock' package. "
                        "Install it with: python -m pip install baostock"
                    )
                if detail.get("type") == "TimeoutError":
                    raise TimeoutError("BaoStock timed out inside its SDK worker.")
                raise TransientProviderError(
                    "BaoStock company metadata request failed: "
                    f"{detail.get('type', 'Error')}: {detail.get('message', '')}".rstrip()
                )
            payload = json.loads(marker.removeprefix("__IRDA_RESULT__"))
            return payload["basic"], payload["industry"]

        bs = self._baostock_module
        try:
            login_result = bs.login()
        except TimeoutError:
            raise
        except Exception as exc:
            raise TransientProviderError(
                f"BaoStock login failed: {type(exc).__name__}."
            ) from exc
        if str(getattr(login_result, "error_code", "1")) != "0":
            raise TransientProviderError(
                "BaoStock login failed: "
                f"{getattr(login_result, 'error_msg', 'unknown provider error')}"
            )

        try:
            basic_result = bs.query_stock_basic(code=code)
            basic_records = _collect_result(basic_result, "stock basic")
            industry_result = bs.query_stock_industry(code=code)
            industry_records = _collect_result(industry_result, "stock industry")
            return basic_records, industry_records
        except (ProviderConfigurationError, TransientProviderError, TimeoutError):
            raise
        except Exception as exc:
            raise TransientProviderError(
                f"BaoStock company metadata request failed for {code}: {type(exc).__name__}."
            ) from exc
        finally:
            try:
                bs.logout()
            except Exception:
                # Do not mask the original query result/error with a logout error.
                pass


class BaoStockCompanyInfoProvider(CompanyInfoProvider):
    def __init__(self, client: BaoStockClient | None = None) -> None:
        self._client = client or BaoStockClient()

    def get_company_info(self, ticker: str) -> dict[str, Any]:
        code = _normalize_a_share_ticker(ticker)
        basic_records, industry_records = self._client.get_company_records(code)
        basic = _find_matching_record(basic_records, _baostock_code(code))
        if basic is None:
            raise ValueError(f"BaoStock returned no company profile for A-share ticker {code!r}.")

        name = _text(_first(basic, ("code_name", "name", "证券简称", "股票名称")))
        if not name:
            raise ValueError(f"BaoStock returned no company name for A-share ticker {code!r}.")
        industry_row = _find_matching_record(industry_records, _baostock_code(code))
        industry = _text(_first(industry_row or {}, ("industry", "industryName", "所属行业")))
        industry_classification = _text(
            _first(industry_row or {}, ("industryClassification", "industry_classification"))
        )
        listing_date = _text(_first(basic, ("ipoDate", "ipo_date", "上市日期")))
        status = _text(_first(basic, ("status", "上市状态")))
        result: dict[str, Any] = {
            "ticker": code,
            "company_name": name,
            "sector": industry,
            "industry": industry,
            "exchange": _exchange_for_code(code),
            "currency": "CNY",
            "source": "BaoStock query_stock_basic/query_stock_industry",
        }
        if listing_date:
            result["listing_date"] = listing_date
        if industry_classification:
            result["industry_classification"] = industry_classification
        if status:
            result["listing_status_code"] = status
        return result


def _collect_result(result: Any, label: str) -> list[dict[str, Any]]:
    error_code = str(getattr(result, "error_code", "0"))
    if error_code != "0":
        raise TransientProviderError(
            f"BaoStock {label} query failed: {getattr(result, 'error_msg', 'unknown provider error')}"
        )
    fields = list(getattr(result, "fields", []) or [])
    rows: list[dict[str, Any]] = []
    try:
        while result.next():
            values = result.get_row_data()
            rows.append(dict(zip(fields, values)))
    except Exception as exc:
        raise TransientProviderError(
            f"BaoStock could not read {label} records: {type(exc).__name__}."
        ) from exc
    return rows


def _normalize_a_share_ticker(ticker: str) -> str:
    if not isinstance(ticker, str):
        raise ValueError("A-share ticker must be a six-digit string.")
    value = ticker.strip().upper()
    value = re.sub(r"^(SH|SZ)", "", value)
    if not re.fullmatch(r"\d{6}", value):
        raise ValueError(f"Invalid A-share ticker {ticker!r}; expected a six-digit code.")
    if value.startswith("6") or value.startswith(("0", "3")):
        return value
    raise ValueError(
        f"BaoStock company metadata supports Shanghai/Shenzhen codes only; got {value!r}."
    )


def _baostock_code(ticker: str) -> str:
    code = _normalize_a_share_ticker(ticker)
    return f"sh.{code}" if code.startswith("6") else f"sz.{code}"


def _find_matching_record(records: list[dict[str, Any]], expected_code: str) -> dict[str, Any] | None:
    for row in records:
        raw_code = _first(row, ("code", "股票代码", "证券代码"))
        if raw_code is None or str(raw_code).strip().lower() == expected_code.lower():
            if raw_code is None and len(records) == 1:
                return row
            if raw_code is not None:
                return row
    return None


def _first(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _exchange_for_code(code: str) -> str:
    return "SSE" if code.startswith("6") else "SZSE"
