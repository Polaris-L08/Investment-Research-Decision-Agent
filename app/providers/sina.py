"""Sina Finance adapter for A-share spot quotes.

This adapter intentionally covers quotes only. Company profiles and financial
statements are not inferred from the quote endpoint and must be supplied by a
separately validated provider.
"""
from __future__ import annotations

import csv
import io
import math
import re
from datetime import datetime
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.providers.config import ProviderConfigurationError
from app.providers.exceptions import TransientProviderError
from app.providers.financial import StockPriceProvider


class SinaFinanceClient:
    """Small injectable client for Sina's legacy A-share quote endpoint."""

    BASE_URL = "https://hq.sinajs.cn/list="

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")
        self._timeout = timeout
        self._opener = opener or urlopen

    def get_quote_text(self, ticker: str) -> str:
        code = _normalize_a_share_ticker(ticker)
        sina_symbol = _sina_symbol(code)
        request = Request(
            f"{self.BASE_URL}{sina_symbol}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
                "Referer": "https://finance.sina.com.cn/",
            },
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                status = getattr(response, "status", 200)
                if status == 429 or status >= 500:
                    raise TransientProviderError(
                        f"Sina Finance returned temporary HTTP status {status}."
                    )
                if status >= 400:
                    raise ProviderConfigurationError(
                        f"Sina Finance quote request failed with HTTP status {status}."
                    )
                raw = response.read()
                headers = getattr(response, "headers", None)
                charset = None
                if headers is not None:
                    try:
                        charset = headers.get_content_charset()
                    except AttributeError:
                        charset = None
        except HTTPError as exc:
            if exc.code == 429 or exc.code >= 500:
                raise TransientProviderError(
                    f"Sina Finance returned temporary HTTP error {exc.code}."
                ) from exc
            raise ProviderConfigurationError(
                f"Sina Finance quote request failed with HTTP {exc.code}."
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise TransientProviderError(
                f"Unable to reach Sina Finance quote endpoint: {type(exc).__name__}."
            ) from exc

        if not raw:
            raise TransientProviderError("Sina Finance returned an empty quote response.")
        encodings = [charset, "utf-8", "gb18030"]
        text = None
        for encoding in encodings:
            if not encoding:
                continue
            try:
                text = raw.decode(encoding)
                break
            except (LookupError, UnicodeDecodeError):
                continue
        if text is None:
            raise TransientProviderError("Sina Finance returned text with an unknown encoding.")
        return text.strip()


class SinaStockPriceProvider(StockPriceProvider):
    """Parse Sina's quote response into the application's provider contract."""

    def __init__(self, client: SinaFinanceClient | None = None) -> None:
        self._client = client or SinaFinanceClient()

    def get_stock_price(self, ticker: str) -> dict[str, Any]:
        code = _normalize_a_share_ticker(ticker)
        expected_symbol = _sina_symbol(code)
        text = self._client.get_quote_text(code)
        match = re.search(r'var\s+hq_str_([a-zA-Z0-9]+)\s*=\s*"([^"]*)"\s*;?', text)
        if not match:
            raise TransientProviderError(
                f"Sina Finance returned an unrecognized quote response for {code}."
            )
        returned_symbol, payload = match.groups()
        if returned_symbol.lower() != expected_symbol:
            raise TransientProviderError(
                f"Sina Finance returned quote symbol {returned_symbol!r} for requested {expected_symbol!r}."
            )
        if not payload.strip():
            raise ValueError(f"No Sina Finance quote data was returned for A-share ticker {code!r}.")

        try:
            fields = next(csv.reader(io.StringIO(payload)))
        except (csv.Error, StopIteration) as exc:
            raise TransientProviderError(
                f"Sina Finance returned malformed quote fields for {code}."
            ) from exc
        if len(fields) < 32:
            raise TransientProviderError(
                f"Sina Finance returned {len(fields)} quote fields for {code}; expected at least 32."
            )

        price = _required_positive_number(fields[3], code, "price")
        trading_date = fields[30].strip() or None
        trading_time = fields[31].strip() or None
        observed_at = datetime.now().astimezone().isoformat(timespec="seconds")
        if trading_date and trading_time and re.fullmatch(r"\d{4}-\d{2}-\d{2}", trading_date):
            # Preserve the source's exchange-local date/time as an explicit
            # field, while observed_at records when this client parsed it.
            source_timestamp = f"{trading_date} {trading_time}"
        else:
            source_timestamp = None

        result: dict[str, Any] = {
            "ticker": code,
            "price": price,
            "latest_trading_day": trading_date,
            "observed_at": observed_at,
            "currency": "CNY",
            "source": "Sina Finance hq.sinajs.cn",
        }
        if source_timestamp:
            result["source_timestamp"] = source_timestamp
        if fields[8].strip():
            result["volume_shares"] = _optional_nonnegative_number(fields[8])
        if fields[9].strip():
            result["turnover_cny"] = _optional_nonnegative_number(fields[9])
        if fields[0].strip():
            result["company_name"] = fields[0].strip()
        return result


def _normalize_a_share_ticker(ticker: str) -> str:
    if not isinstance(ticker, str):
        raise ValueError("A-share ticker must be a six-digit string.")
    value = ticker.strip().upper()
    value = re.sub(r"^(SH|SZ|BJ)", "", value)
    if not re.fullmatch(r"\d{6}", value):
        raise ValueError(
            f"Invalid A-share ticker {ticker!r}; expected a six-digit code such as '600000'."
        )
    if value.startswith("6") or value.startswith("0") or value.startswith("3"):
        return value
    if value.startswith(("4", "8")) or value.startswith("920"):
        return value
    raise ValueError(
        f"Unsupported A-share ticker prefix for Sina Finance: {value!r}. "
        "Supported prefixes are Shanghai (6), Shenzhen (0/3), and Beijing (4/8/920)."
    )


def _sina_symbol(code: str) -> str:
    if code.startswith("6"):
        return f"sh{code}"
    if code.startswith(("0", "3")):
        return f"sz{code}"
    if code.startswith(("4", "8")) or code.startswith("920"):
        return f"bj{code}"
    raise ValueError(f"Unsupported A-share ticker for Sina Finance: {code!r}.")


def _required_positive_number(raw: Any, ticker: str, field: str) -> float:
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise TransientProviderError(
            f"Sina Finance returned an invalid {field} for {ticker}."
        ) from exc
    if not math.isfinite(value) or value <= 0:
        raise TransientProviderError(
            f"Sina Finance returned a non-positive or non-finite {field} for {ticker}."
        )
    return value


def _optional_nonnegative_number(raw: Any) -> float | None:
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return value
