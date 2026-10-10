"""Manually verify Alpha Vantage quote/profile access using a real API key.

Usage (from project root, after configuring .env):
    python scripts/smoke_test_real_providers.py AAPL
"""

import argparse
import json

from app.providers.config import ProviderSettings
from app.providers.factory import create_provider_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", nargs="?", default="AAPL", help="ticker symbol to query")
    args = parser.parse_args()

    settings = ProviderSettings.from_env()
    if settings.mode != "real":
        parser.error("Set PROVIDER_MODE=real in .env before running this smoke test.")

    bundle = create_provider_bundle(settings)
    print("Provider bundle:", bundle.mode)
    print("Stock quote:")
    print(json.dumps(bundle.stock_price.get_stock_price(args.ticker), indent=2))
    print("Company profile:")
    print(json.dumps(bundle.company_info.get_company_info(args.ticker), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
