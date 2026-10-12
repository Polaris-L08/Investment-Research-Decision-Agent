"""Sina Finance annual income-statement adapter using AKShare's Sina wrapper.

The wrapper is used only as an HTTP/HTML parsing dependency. This provider does
not use AKShare's Eastmoney endpoints for financial statements.
"""
from __future__ import annotations

import math
import re
import threading
from typing import Any

from app.providers.config import ProviderConfigurationError
from app.providers.exceptions import TransientProviderError
from app.providers.financial import RevenueInfoProvider, NetIncomeInfoProvider


class SinaFinancialStatementClient:
    """Fetch the Sina income statement lazily through AKShare's Sina endpoint."""

    def __init__(self, ak_module: Any | None = None) -> None:
        self._ak_module = ak_module

    def _module(self) -> Any:
        if self._ak_module is not None:
            return self._ak_module
        try:
            import akshare as ak
        except ImportError as exc:
            raise ProviderConfigurationError(
                "REAL_PROVIDER_SOURCE=sina_baostock requires the optional 'akshare' package "
                "for Sina's financial-statement parser. Install it with: "
                "python -m pip install -r requirements-akshare.txt"
            ) from exc
        self._ak_module = ak
        return ak

    def get_income_statement_records(self, ticker: str) -> list[dict[str, Any]]:
        code = _normalize_a_share_ticker(ticker)
        symbol = _sina_symbol(code)
        ak = self._module()
        try:
            frame = ak.stock_financial_report_sina(stock=symbol, symbol="利润表")
            return _records(frame)
        except ProviderConfigurationError:
            raise
        except Exception as exc:
            raise TransientProviderError(
                f"Sina Finance income-statement request failed for {code}: {type(exc).__name__}."
            ) from exc


class SinaIncomeStatementProvider(RevenueInfoProvider, NetIncomeInfoProvider):
    """Provide latest annual total operating revenue and net income from Sina."""

    def __init__(self, client: SinaFinancialStatementClient | None = None) -> None:
        self._client = client or SinaFinancialStatementClient()
        self._reports: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get_revenue(self, ticker: str) -> float:
        return self.get_latest_annual_report(ticker)["revenue"]

    def get_net_income(self, ticker: str) -> float:
        return self.get_latest_annual_report(ticker)["net_income"]

    def get_latest_annual_report(self, ticker: str) -> dict[str, Any]:
        code = _normalize_a_share_ticker(ticker)
        with self._lock:
            cached = self._reports.get(code)
            if cached is not None:
                return dict(cached)

            records = self._client.get_income_statement_records(code)
            annual: list[tuple[str, dict[str, Any]]] = []
            for row in records:
                report_date = _first(row, ("报告日", "报告日期", "报告期", "报告时间", "日期", "REPORT_DATE"))
                normalized_date = _normalize_report_date(report_date)
                if normalized_date and normalized_date.endswith("-12-31"):
                    annual.append((normalized_date, row))
            if not annual:
                raise ValueError(
                    f"Sina Finance returned no annual (December 31) income-statement record for {code}."
                )

            report_date, row = max(annual, key=lambda item: item[0])
            revenue_field = _find_field(row, ("营业总收入", "营业总收入(元)", "营业收入", "营业收入(元)"))
            net_income_field = _find_field(row, ("净利润", "净利润(元)", "归属于母公司所有者的净利润"))
            revenue = _required_finite_number(row.get(revenue_field), code, "annual operating revenue")
            net_income = _required_finite_number(row.get(net_income_field), code, "annual net income")
            if revenue < 0:
                raise TransientProviderError(
                    f"Sina Finance returned a negative annual revenue for {code}."
                )

            result = {
                "ticker": code,
                "fiscal_date_ending": report_date,
                "revenue": revenue,
                "net_income": net_income,
                "period": "annual",
                "currency": "CNY",
                "unit": "CNY",
                "revenue_metric": "total_operating_revenue" if "总" in revenue_field else "operating_revenue",
                "net_income_metric": net_income_field,
                "source": "Sina Finance stock_financial_report_sina (income statement)",
            }
            publication_date = _first(row, ("公告日期", "发布日期", "pubDate"))
            if publication_date:
                result["publication_date"] = str(publication_date).strip()
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
            rows = frame.to_dict(orient="records")
            if isinstance(rows, list):
                return [dict(row) for row in rows if isinstance(row, dict)]
        except TypeError:
            pass
    raise TransientProviderError("Sina Finance returned an unsupported income-statement table.")


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
        f"Sina financial statements currently support Shanghai/Shenzhen A-share codes only; got {value!r}."
    )


def _sina_symbol(code: str) -> str:
    return f"sh{code}" if code.startswith("6") else f"sz{code}"


def _normalize_report_date(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if re.fullmatch(r"\d{8}(?:\.0)?", raw):
        raw = raw[:8]
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    match = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?:\s.*)?", raw)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return None


def _find_field(row: dict[str, Any], candidates: tuple[str, ...]) -> str:
    for candidate in candidates:
        if candidate in row and row[candidate] not in (None, ""):
            return candidate
    raise ValueError(
        "Sina Finance income statement is missing a required field; expected one of: "
        + ", ".join(candidates)
    )


def _required_finite_number(value: Any, ticker: str, field: str) -> float:
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError) as exc:
        raise TransientProviderError(
            f"Sina Finance returned an invalid {field} for {ticker}."
        ) from exc
    if not math.isfinite(number):
        raise TransientProviderError(
            f"Sina Finance returned a non-finite {field} for {ticker}."
        )
    return number


def _first(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None
