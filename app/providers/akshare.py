"""AKShare adapters for A-share quotes, company profiles, and annual financials.

AKShare is an optional dependency. Importing this module does not require it;
the library is loaded only when a real request is made, which keeps unit tests
and Mock mode independent from network/data-provider packages.
"""
from __future__ import annotations

from datetime import datetime
import importlib
import math
import re
import threading
from typing import Any, Callable

from app.providers.config import ProviderConfigurationError
from app.providers.exceptions import TransientProviderError
from app.providers.financial import (
    CompanyInfoProvider,
    NetIncomeInfoProvider,
    RevenueInfoProvider,
    StockPriceProvider,
)


class AkShareClient:
    """Thin, injectable wrapper around the optional ``akshare`` package."""

    def __init__(
        self,
        ak_module: Any | None = None,
        *,
        clock: Callable[[], float] | None = None,
        cache_ttl_seconds: float = 60.0,
    ) -> None:
        self._ak_module = ak_module
        self._clock = clock
        self._cache_ttl_seconds = max(0.0, float(cache_ttl_seconds))
        self._snapshot_cache: tuple[float, list[dict[str, Any]]] | None = None
        self._cache_lock = threading.Lock()

    def _ak(self) -> Any:
        if self._ak_module is None:
            try:
                self._ak_module = importlib.import_module("akshare")
            except ImportError as exc:
                raise ProviderConfigurationError(
                    "REAL_PROVIDER_SOURCE=akshare requires the optional 'akshare' package. "
                    "Install it in the active virtual environment with: python -m pip install akshare"
                ) from exc
        return self._ak_module

    def _now(self) -> float:
        if self._clock is not None:
            return self._clock()
        import time
        return time.monotonic()

    def get_a_share_spot_records(self) -> list[dict[str, Any]]:
        """Return a cached all-market spot snapshot to avoid one download per ticker."""
        with self._cache_lock:
            now = self._now()
            if self._snapshot_cache is not None:
                cached_at, records = self._snapshot_cache
                if now - cached_at <= self._cache_ttl_seconds:
                    return records

            try:
                frame = self._ak().stock_zh_a_spot_em()
                records = _records(frame)
            except ProviderConfigurationError:
                raise
            except Exception as exc:
                raise TransientProviderError(
                    f"AKShare A-share spot snapshot request failed: {exc}"
                ) from exc

            if not records:
                raise TransientProviderError(
                    "AKShare returned an empty A-share spot snapshot."
                )
            self._snapshot_cache = (now, records)
            return records

    def get_individual_info_records(self, ticker: str) -> list[dict[str, Any]]:
        code = _normalize_a_share_ticker(ticker)
        try:
            return _records(self._ak().stock_individual_info_em(symbol=code))
        except ProviderConfigurationError:
            raise
        except Exception as exc:
            raise TransientProviderError(
                f"AKShare company-profile request failed for {code}: {exc}"
            ) from exc

    def get_profit_statement_records(self, ticker: str) -> list[dict[str, Any]]:
        code = _normalize_a_share_ticker(ticker)
        try:
            return _records(self._ak().stock_profit_sheet_by_report_em(symbol=code))
        except ProviderConfigurationError:
            raise
        except Exception as exc:
            raise TransientProviderError(
                f"AKShare profit-statement request failed for {code}: {exc}"
            ) from exc


class AkShareStockPriceProvider(StockPriceProvider):
    def __init__(self, client: AkShareClient | None = None) -> None:
        self._client = client or AkShareClient()

    def get_stock_price(self, ticker: str) -> dict[str, Any]:
        code = _normalize_a_share_ticker(ticker)
        records = self._client.get_a_share_spot_records()
        row = _find_record(records, ("代码", "股票代码", "证券代码", "symbol"), code)
        if row is None:
            raise ValueError(f"No A-share spot quote was returned for ticker {code!r}.")

        price = _required_number(_first(row, ("最新价", "现价", "最新", "收盘")), code, "price")
        if price <= 0:
            raise TransientProviderError(f"AKShare returned a non-positive price for {code}.")
        return {
            "ticker": code,
            "price": price,
            # The all-market spot endpoint does not consistently provide a
            # quote timestamp, so do not fabricate a trading date.
            "latest_trading_day": None,
            "observed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "currency": "CNY",
            "source": "AKShare stock_zh_a_spot_em (Eastmoney)",
        }


class AkShareCompanyInfoProvider(CompanyInfoProvider):
    def __init__(self, client: AkShareClient | None = None) -> None:
        self._client = client or AkShareClient()

    def get_company_info(self, ticker: str) -> dict[str, Any]:
        code = _normalize_a_share_ticker(ticker)
        records = self._client.get_individual_info_records(code)
        values: dict[str, Any] = {}
        for row in records:
            key = _first(row, ("item", "项目", "指标"))
            value = _first(row, ("value", "值", "数据"))
            if key is not None:
                values[str(key).strip()] = value

        name = _optional_text(_mapping_value(values, ("股票简称", "证券简称", "名称")))
        if not name:
            raise ValueError(f"No company name was returned for A-share ticker {code!r}.")
        market_cap = _optional_number(_mapping_value(values, ("总市值", "总市值(元)")))
        return {
            "ticker": code,
            "company_name": name,
            "sector": _optional_text(_mapping_value(values, ("行业", "所属行业"))),
            "industry": _optional_text(_mapping_value(values, ("行业", "所属行业"))),
            "exchange": _exchange_for_code(code),
            "currency": "CNY",
            "market_cap": market_cap,
            "listing_date": _optional_text(_mapping_value(values, ("上市时间", "上市日期"))),
            "source": "AKShare stock_individual_info_em (Eastmoney)",
        }


class AkShareIncomeStatementProvider(RevenueInfoProvider, NetIncomeInfoProvider):
    """Provides revenue and net income from the same latest annual report."""

    def __init__(self, client: AkShareClient | None = None) -> None:
        self._client = client or AkShareClient()
        self._reports: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get_revenue(self, ticker: str) -> float:
        return self.get_latest_annual_report(ticker)["revenue"]

    def get_net_income(self, ticker: str) -> float:
        return self.get_latest_annual_report(ticker)["net_income"]

    def get_latest_annual_report(self, ticker: str) -> dict[str, Any]:
        code = _normalize_a_share_ticker(ticker)
        with self._lock:
            if code in self._reports:
                return dict(self._reports[code])

            records = self._client.get_profit_statement_records(code)
            annual_records: list[tuple[str, dict[str, Any]]] = []
            for row in records:
                report_date = _optional_text(_first(
                    row, ("报告日期", "报告期", "报告时间", "REPORT_DATE", "REPORT_PERIOD", "日期")
                ))
                normalized_date = _normalize_report_date(report_date)
                if normalized_date and normalized_date.endswith("-12-31"):
                    annual_records.append((normalized_date, row))

            if not annual_records:
                raise ValueError(
                    f"AKShare returned no annual (December 31) profit-statement record for {code}."
                )
            report_date, row = max(annual_records, key=lambda item: item[0])
            revenue = _required_number(
                _first(row, ("营业总收入", "营业收入", "营业总收入-营业总收入", "OPERATE_INCOME")),
                code,
                "annual revenue",
            )
            net_income = _required_number(
                _first(row, ("净利润", "净利润-净利润", "NETPROFIT", "NET_PROFIT")),
                code,
                "annual net income",
            )
            result = {
                "ticker": code,
                "fiscal_date_ending": report_date,
                "revenue": revenue,
                "net_income": net_income,
                "period": "annual",
                "currency": "CNY",
                "unit": "CNY",
                "source": "AKShare stock_profit_sheet_by_report_em (Eastmoney)",
            }
            self._reports[code] = result
            return dict(result)


def _records(frame: Any) -> list[dict[str, Any]]:
    if frame is None:
        return []
    if isinstance(frame, list):
        return [dict(row) for row in frame if isinstance(row, dict)]
    if isinstance(frame, dict):
        return [frame]
    if getattr(frame, "empty", False):
        return []
    if hasattr(frame, "to_dict"):
        try:
            result = frame.to_dict(orient="records")
            if isinstance(result, list):
                return [dict(row) for row in result if isinstance(row, dict)]
        except TypeError:
            pass
    if hasattr(frame, "iterrows") and hasattr(frame, "columns"):
        return [dict(row) for _, row in frame.iterrows()]
    raise TransientProviderError("AKShare returned an unsupported table structure.")


def _normalize_a_share_ticker(ticker: str) -> str:
    if not isinstance(ticker, str):
        raise ValueError("A-share ticker must be a six-digit string.")
    value = ticker.strip().upper()
    value = re.sub(r"^(SH|SZ|BJ)", "", value)
    if not re.fullmatch(r"\d{6}", value):
        raise ValueError(
            f"Invalid A-share ticker {ticker!r}; expected a six-digit code such as '000001'."
        )
    return value


def _exchange_for_code(code: str) -> str:
    if code.startswith(("6",)):
        return "SSE"
    if code.startswith(("0", "3")):
        return "SZSE"
    if code.startswith(("4", "8", "9")):
        return "BSE"
    if code.startswith(("00", "30")):
        return "SZSE"
    if code.startswith(("68",)):
        return "SSE"
    return "UNKNOWN"


def _find_record(records: list[dict[str, Any]], key_names: tuple[str, ...], ticker: str) -> dict[str, Any] | None:
    for row in records:
        raw_code = _first(row, key_names)
        if raw_code is None:
            continue
        try:
            normalized = _normalize_a_share_ticker(str(raw_code))
        except ValueError:
            continue
        if normalized == ticker:
            return row
    return None


def _first(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return None


def _mapping_value(mapping: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in mapping and mapping[name] is not None:
            return mapping[name]
    return None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text and text.lower() not in {"nan", "none", "--", "-"} else None


def _optional_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "--", "-"}:
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _required_number(value: Any, ticker: str, label: str) -> float:
    number = _optional_number(value)
    if number is None:
        raise TransientProviderError(
            f"AKShare returned a missing or invalid {label} value for {ticker}."
        )
    return number


def _normalize_report_date(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    # Handle timestamps and common date strings without guessing non-date labels.
    match = re.search(r"(\d{4})[-/.年]?(\d{2})[-/.月]?(\d{2})日?", text)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{year}-{month}-{day}"
