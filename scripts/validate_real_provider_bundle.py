"""Validate the integrated real A-share provider bundle against data contracts.

This is an opt-in network test. It deliberately runs quote, company profile,
and annual financial checks together so provider integrations are accepted as
one capability rather than as unrelated lessons.

Examples:
    python scripts/validate_real_provider_bundle.py
    python scripts/validate_real_provider_bundle.py --tickers 600000,000001
    python scripts/validate_real_provider_bundle.py --tickers 600000 --max-quote-age-days 10
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from datetime import date, datetime
from typing import Any

from app.providers.config import ProviderSettings
from app.providers.factory import create_provider_bundle


def _as_finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _parse_iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _parse_publication_date(value: Any) -> date | None:
    if value is None:
        return None
    raw = str(value).strip()
    if re.fullmatch(r"\d{8}", raw):
        try:
            return datetime.strptime(raw, "%Y%m%d").date()
        except ValueError:
            return None
    return _parse_iso_date(raw)


def validate_quote(
    quote: dict[str, Any], *, ticker: str, today: date, max_age_days: int
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for field in ("ticker", "price", "price_basis", "latest_trading_day", "currency", "source"):
        if field not in quote or quote[field] in (None, ""):
            errors.append(f"quote missing required field: {field}")

    if str(quote.get("ticker", "")).strip() != ticker:
        errors.append(f"quote ticker mismatch: expected {ticker}, got {quote.get('ticker')!r}")

    price = _as_finite_number(quote.get("price"))
    if price is None or price <= 0:
        errors.append("quote price must be a finite positive number")

    price_basis = quote.get("price_basis")
    if price_basis not in {"current", "previous_close"}:
        errors.append("quote price_basis must be 'current' or 'previous_close'")
    elif price_basis == "previous_close":
        warnings.append("quote uses previous-close fallback; do not treat it as a live price")

    trading_day = _parse_iso_date(quote.get("latest_trading_day"))
    if trading_day is None:
        errors.append("quote latest_trading_day must be an ISO date (YYYY-MM-DD)")
    else:
        age_days = (today - trading_day).days
        if age_days < 0:
            errors.append("quote latest_trading_day is in the future")
        elif age_days > max_age_days:
            errors.append(
                f"quote is stale: latest trading day is {age_days} calendar days old "
                f"(limit {max_age_days})"
            )

    if quote.get("currency") != "CNY":
        errors.append(f"A-share quote currency must be CNY, got {quote.get('currency')!r}")

    observed_at = quote.get("observed_at")
    if not isinstance(observed_at, str):
        errors.append("quote observed_at is missing or not a string")
    else:
        try:
            datetime.fromisoformat(observed_at)
        except ValueError:
            errors.append("quote observed_at must be an ISO datetime with timezone information")
        else:
            if datetime.fromisoformat(observed_at).tzinfo is None:
                errors.append("quote observed_at must include timezone information")

    return errors, warnings


def validate_company_profile(profile: dict[str, Any], *, ticker: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for field in ("ticker", "company_name", "exchange", "currency", "source", "listing_date"):
        if profile.get(field) in (None, ""):
            errors.append(f"company profile missing required field: {field}")
    if str(profile.get("ticker", "")).strip() != ticker:
        errors.append(f"company profile ticker mismatch: expected {ticker}, got {profile.get('ticker')!r}")
    if profile.get("currency") != "CNY":
        errors.append(f"company profile currency must be CNY, got {profile.get('currency')!r}")
    if profile.get("exchange") not in {"SSE", "SZSE"}:
        errors.append(f"unsupported company profile exchange: {profile.get('exchange')!r}")
    listing_date = _parse_iso_date(profile.get("listing_date"))
    if listing_date is None:
        errors.append("company profile listing_date must be an ISO date (YYYY-MM-DD)")
    elif listing_date > date.today():
        errors.append("company profile listing_date is in the future")
    if not profile.get("industry") and not profile.get("sector"):
        warnings.append("company profile has no industry/sector classification")
    return errors, warnings


def validate_annual_report(
    report: dict[str, Any], *, ticker: str, today: date
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for field in (
        "ticker", "fiscal_date_ending", "revenue", "net_income", "period",
        "currency", "unit", "revenue_metric", "net_income_metric", "source",
    ):
        if report.get(field) in (None, ""):
            errors.append(f"annual report missing required field: {field}")
    if str(report.get("ticker", "")).strip() != ticker:
        errors.append(f"annual report ticker mismatch: expected {ticker}, got {report.get('ticker')!r}")
    fiscal_date = _parse_iso_date(report.get("fiscal_date_ending"))
    if fiscal_date is None:
        errors.append("annual report fiscal_date_ending must be an ISO date")
    elif fiscal_date.month != 12 or fiscal_date.day != 31:
        errors.append("annual report fiscal_date_ending must be December 31")
    elif fiscal_date > today:
        errors.append("annual report fiscal_date_ending is in the future")
    elif fiscal_date.year < today.year - 1:
        warnings.append(
            f"latest annual report is for {fiscal_date.year}; confirm that a newer annual report is not available"
        )

    revenue = _as_finite_number(report.get("revenue"))
    if revenue is None or revenue < 0:
        errors.append("annual report revenue must be a finite non-negative number")
    net_income = _as_finite_number(report.get("net_income"))
    if net_income is None:
        errors.append("annual report net_income must be a finite number")
    if report.get("period") != "annual":
        errors.append("financial report period must be 'annual'")
    if report.get("currency") != "CNY" or report.get("unit") != "CNY":
        errors.append("annual report must explicitly declare CNY currency and unit")
    publication_date = _parse_publication_date(report.get("publication_date"))
    if report.get("publication_date") not in (None, "") and publication_date is None:
        errors.append("annual report publication_date has an unsupported or invalid format")
    elif publication_date is None:
        warnings.append("annual report does not expose a publication_date")
    elif publication_date > today:
        errors.append("annual report publication_date is in the future")
    return errors, warnings


def _run_one(bundle: Any, ticker: str, today: date, max_age_days: int) -> tuple[int, int]:
    failures = 0
    warnings_total = 0
    print(f"\n=== {ticker} ===")

    checks = (
        ("quote", lambda: bundle.stock_price.get_stock_price(ticker), validate_quote),
        ("company profile", lambda: bundle.company_info.get_company_info(ticker), validate_company_profile),
        ("annual financials", lambda: bundle.revenue.get_latest_annual_report(ticker), validate_annual_report),
    )
    for label, fetch, validator in checks:
        try:
            result = fetch()
            if not isinstance(result, dict):
                raise TypeError(f"provider returned {type(result).__name__}, expected dict")
            if label == "quote":
                errors, warnings = validator(result, ticker=ticker, today=today, max_age_days=max_age_days)
            elif label == "annual financials":
                errors, warnings = validator(result, ticker=ticker, today=today)
            else:
                errors, warnings = validator(result, ticker=ticker)
            status = "FAIL" if errors else ("WARN" if warnings else "PASS")
            print(f"[{status}] {label}")
            if label == "quote":
                print(
                    "  price={price!r} basis={basis!r} trading_day={day!r} source={source!r}".format(
                        price=result.get("price"), basis=result.get("price_basis"),
                        day=result.get("latest_trading_day"), source=result.get("source"),
                    )
                )
            elif label == "company profile":
                print(
                    "  name={name!r} exchange={exchange!r} listing_date={listing!r} source={source!r}".format(
                        name=result.get("company_name"), exchange=result.get("exchange"),
                        listing=result.get("listing_date"), source=result.get("source"),
                    )
                )
            else:
                print(
                    "  fiscal_date={fiscal!r} revenue={revenue!r} net_income={income!r} publication_date={published!r}".format(
                        fiscal=result.get("fiscal_date_ending"), revenue=result.get("revenue"),
                        income=result.get("net_income"), published=result.get("publication_date"),
                    )
                )
            for warning in warnings:
                print(f"  WARNING: {warning}")
            for error in errors:
                print(f"  ERROR: {error}")
            failures += len(errors)
            warnings_total += len(warnings)
        except Exception as exc:  # noqa: BLE001 - validation runner must continue to next capability/ticker
            failures += 1
            print(f"[FAIL] {label}: {type(exc).__name__}: {exc}")

    return failures, warnings_total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tickers", default="600000,000001,300750",
        help="comma-separated Shanghai/Shenzhen A-share codes (default: 600000,000001,300750)",
    )
    parser.add_argument(
        "--max-quote-age-days", type=int, default=7,
        help="maximum allowed calendar-day age for quote's latest trading day (default: 7)",
    )
    args = parser.parse_args()
    tickers = [part.strip() for part in args.tickers.split(",") if part.strip()]
    if not tickers:
        parser.error("Provide at least one ticker via --tickers.")
    if args.max_quote_age_days < 0:
        parser.error("--max-quote-age-days must be non-negative.")

    settings = ProviderSettings.from_env()
    if settings.mode != "real":
        parser.error("Set PROVIDER_MODE=real in .env before running this validation.")
    if settings.real_provider_source != "sina_baostock":
        parser.error("This integrated A-share validation requires REAL_PROVIDER_SOURCE=sina_baostock.")

    bundle = create_provider_bundle(settings)
    today = datetime.now().astimezone().date()
    print("Provider bundle:", bundle.mode)
    print("Provider source:", settings.real_provider_source)
    print("Validation date:", today.isoformat())
    print("Tickers:", ", ".join(tickers))
    print("Maximum quote age (calendar days):", args.max_quote_age_days)

    failures = 0
    warnings = 0
    for ticker in tickers:
        code = ticker.strip().upper()
        code = re.sub(r"^(SH|SZ)", "", code)
        ticker_failures, ticker_warnings = _run_one(bundle, code, today, args.max_quote_age_days)
        failures += ticker_failures
        warnings += ticker_warnings

    print("\n=== Summary ===")
    print(f"Tickers checked: {len(tickers)}")
    print(f"Validation errors: {failures}")
    print(f"Warnings: {warnings}")
    if failures:
        print("RESULT: FAIL — resolve errors before accepting the real-data integration.")
        return 1
    print("RESULT: PASS WITH WARNINGS" if warnings else "RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
