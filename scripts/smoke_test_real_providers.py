"""Manually verify the configured real provider with a live request.

Alpha Vantage: REAL_PROVIDER_SOURCE=alpha_vantage and ALPHA_VANTAGE_API_KEY set.
AKShare:       REAL_PROVIDER_SOURCE=akshare (no API key; use a six-digit A-share code).
Usage:         python scripts/smoke_test_real_providers.py [ticker]
"""

import argparse
import json

from app.providers.config import ProviderSettings
from app.providers.factory import create_provider_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", nargs="?", default=None, help="ticker symbol/code; defaults to AAPL for Alpha Vantage or 000001 for AKShare")
    args = parser.parse_args()

    settings = ProviderSettings.from_env()
    if settings.mode != "real":
        parser.error("Set PROVIDER_MODE=real in .env before running this smoke test.")

    ticker = args.ticker or ("000001" if settings.real_provider_source == "akshare" else "AAPL")
    bundle = create_provider_bundle(settings)
    print("Provider bundle:", bundle.mode)
    print("Provider source:", settings.real_provider_source)
    print("Ticker:", ticker)
    print("Stock quote:")
    print(json.dumps(bundle.stock_price.get_stock_price(ticker), indent=2, ensure_ascii=False))
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
