from app.tools.financial import (
    get_company_info,
    get_stock_price, get_revenue, get_net_income,
)


COMPANY_RESEARCH_TOOLS = [
    get_company_info,
    get_stock_price,
]

FINANCIAL_RESEARCH_TOOLS = [
    get_revenue,
    get_net_income,
]