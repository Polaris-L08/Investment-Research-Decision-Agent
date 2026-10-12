"""Manually verify the configured real provider with a live request.

Alpha Vantage: REAL_PROVIDER_SOURCE=alpha_vantage and ALPHA_VANTAGE_API_KEY set.
AKShare:       REAL_PROVIDER_SOURCE=akshare (A-share quote/profile/financial adapters).
Sina Finance:  REAL_PROVIDER_SOURCE=sina (A-share quote only; six-digit code).
Sina+BaoStock: REAL_PROVIDER_SOURCE=sina_baostock (Sina quote/income statement; BaoStock company metadata).
Usage:         python scripts/smoke_test_real_providers.py [ticker]
"""

import argparse
import json

from app.providers.config import ProviderSettings
from app.providers.factory import create_provider_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", nargs="?", default=None, help="ticker symbol/code; defaults to AAPL for Alpha Vantage or 600000 for A-share sources")
    args = parser.parse_args()

    settings = ProviderSettings.from_env()
    if settings.mode != "real":
        parser.error("Set PROVIDER_MODE=real in .env before running this smoke test.")

    default_tickers = {
        "alpha_vantage": "AAPL",
        "akshare": "000001",
        "sina": "600000",
        "sina_baostock": "600000",
    }
    ticker = args.ticker or default_tickers[settings.real_provider_source]
    bundle = create_provider_bundle(settings)
    print("Provider bundle:", bundle.mode)
    print("Provider source:", settings.real_provider_source)
    print("Ticker:", ticker)
    print("Stock quote:")
    print(json.dumps(bundle.stock_price.get_stock_price(ticker), indent=2, ensure_ascii=False))
    if settings.real_provider_source == "sina":
        print("Company profile: intentionally unavailable for source 'sina'.")
        print("Annual financials: intentionally unavailable for source 'sina'.")
        print("This smoke test validates quote connectivity only; it does not imply full data coverage.")
        return 0

    print("Company profile:")
    print(json.dumps(bundle.company_info.get_company_info(ticker), indent=2, ensure_ascii=False))
    print("Latest annual financials:")
    statement_provider = bundle.revenue
    if hasattr(statement_provider, "get_latest_annual_report"):
        print(json.dumps(statement_provider.get_latest_annual_report(ticker), indent=2, ensure_ascii=False))
    else:
        print(json.dumps({
            "ticker": ticker.upper(),
            "revenue": bundle.revenue.get_revenue(ticker),
            "net_income": bundle.net_income.get_net_income(ticker),
            "period": "annual",
            "source": "configured provider income statement",
        }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
