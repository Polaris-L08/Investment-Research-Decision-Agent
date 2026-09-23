from pydantic import BaseModel, Field


class ResearchSummary(BaseModel):
    summary: str = Field(
        description="A concise summary of the investment research."
    )

    key_factors: list[str] = Field(
        description="The key factors that materially affect the investment analysis."
    )