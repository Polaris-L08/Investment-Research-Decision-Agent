from pydantic import BaseModel, Field


class CompanyResearchResult(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol."
    )

    company_name: str = Field(
        description="Company name."
    )

    sector: str = Field(
        description="Primary business sector."
    )

    current_price: float = Field(
        description="Current stock price."
    )

    summary: str = Field(
        description="Concise factual company research summary."
    )


class FinancialResearchResult(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol."
    )

    revenue: float = Field(
        description="Company revenue."
    )

    net_income: float = Field(
        description="Company net income."
    )

    profit_margin: float = Field(
        description="Net income divided by revenue."
    )

    summary: str = Field(
        description="Concise factual financial research summary."
    )