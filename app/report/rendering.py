from app.report.models import InvestmentReport


def render_markdown(report: InvestmentReport) -> str:
    """Render a completed InvestmentReport as Markdown."""

    return "\n".join(
        [
            f"# {report.title}",
            "",
            "## Executive Summary",
            "",
            report.executive_summary,
            "",
            "## Company Overview",
            "",
            report.company_overview,
            "",
            "## Financial Summary",
            "",
            report.financial_summary,
            "",
            "## Market Summary",
            "",
            report.market_summary,
            "",
            "## Industry & Macro Summary",
            "",
            report.industry_macro_summary,
            "",
            "## Valuation Summary",
            "",
            report.valuation_summary,
            "",
            "## Risk Summary",
            "",
            report.risk_summary,
            "",
            "## Investment Decision",
            "",
            report.investment_decision_summary,
        ]
    )