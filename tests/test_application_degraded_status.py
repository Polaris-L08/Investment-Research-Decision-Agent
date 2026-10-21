from unittest.mock import patch

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.application.graph import finalize_application, run_research_stage


def _research_result(status="complete", reason=""):
    company = CompanyResearchResult(
        ticker="AAPL", company_name="Apple", sector="Technology",
        current_price=200.0, summary="Company evidence.",
        data_status=status, degradation_reason=reason,
    )
    return {
        "research_plan": None,
        "completed_research_areas": [],
        "company_research": company,
        "financial_research": FinancialResearchResult(
            ticker="AAPL", revenue=100.0, net_income=20.0,
            profit_margin=0.2, summary="Financial evidence.",
        ),
        "market_research": MarketResearchResult(
            ticker="AAPL", market_index="S&P 500", market_return=0.1,
            summary="Market evidence.",
        ),
        "industry_macro_research": IndustryMacroResearchResult(
            ticker="AAPL", industry="Technology", industry_growth=0.1,
            macro_environment="Stable", macro_growth=0.02,
            summary="Industry evidence.",
        ),
        "research_errors": {},
        "planning_error": "",
        "supervisor_error": "",
        "valuation_inputs": None,
        "valuation_assumptions": None,
        "valuation_research_error": "",
    }


def test_application_aggregates_degraded_research_status():
    payload = _research_result("degraded", "LLM synthesis failed; provider data retained.")
    with patch("app.application.graph.research_supervisor_graph.invoke", return_value=payload):
        result = run_research_stage({"ticker": "AAPL", "user_query": "Research Apple"})

    assert result["research_data_status"] == "degraded"
    assert result["degraded_research_areas"] == ["company"]
    assert result["research_degradation_reasons"] == {
        "company": "LLM synthesis failed; provider data retained."
    }
    assert result["company_research"].data_status == "degraded"
    assert result["current_stage"] == "valuation"


def test_application_reports_complete_when_all_research_results_are_complete():
    payload = _research_result()
    with patch("app.application.graph.research_supervisor_graph.invoke", return_value=payload):
        result = run_research_stage({"ticker": "AAPL", "user_query": "Research Apple"})

    assert result["research_data_status"] == "complete"
    assert result["degraded_research_areas"] == []
    assert result["research_degradation_reasons"] == {}


def test_public_output_preserves_aggregate_degradation_status():
    result = finalize_application({
        "ticker": "AAPL",
        "research_data_status": "degraded",
        "degraded_research_areas": ["company"],
        "research_degradation_reasons": {"company": "synthesis failed"},
    })
    assert result["research_data_status"] == "degraded"
    assert result["degraded_research_areas"] == ["company"]
    assert result["research_degradation_reasons"] == {"company": "synthesis failed"}


def test_report_markdown_discloses_degraded_research_input():
    from app.application.graph import run_report_stage

    raw = {
        "report": None,
        "report_assembly_error": "",
        "report_generation_error": "",
        "report_merge_error": "",
        "report_rendering_error": "",
        "report_markdown": "# Investment Report\nNormal narrative.",
    }
    state = {
        "degraded_research_areas": ["company"],
        "research_degradation_reasons": {"company": "LLM synthesis failed; provider data retained."},
        "stage_errors": {},
    }
    with patch("app.application.graph.report_graph.invoke", return_value=raw):
        result = run_report_stage(state)

    assert result["report_markdown"].startswith("## Research data limitations")
    assert "company: LLM synthesis failed; provider data retained." in result["report_markdown"]
    assert "Normal narrative." in result["report_markdown"]


def test_final_output_does_not_default_failed_or_unreached_research_to_complete():
    result = finalize_application({"ticker": "AAPL", "application_error": "research failed"})
    assert result["research_data_status"] == "not_available"
