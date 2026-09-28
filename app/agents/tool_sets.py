from app.tools.financial import (
    get_company_info,
    get_stock_price, get_revenue, get_net_income, get_market_index, get_market_return,
)


COMPANY_RESEARCH_TOOLS = [
    get_company_info,
    get_stock_price,
]

FINANCIAL_RESEARCH_TOOLS = [
    get_revenue,
    get_net_income,
]

MARKET_RESEARCH_TOOLS = [
    get_market_index,
    get_market_return,
]