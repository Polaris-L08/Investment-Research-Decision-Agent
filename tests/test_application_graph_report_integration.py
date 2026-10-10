"""Focused tests for the M6 Report Graph integration boundary."""

import app.application.graph as application_graph_module
from app.application.graph import build_application_graph, run_report_stage
from app.report.models import InvestmentReport
from test_report_generation import build_test_report


def test_application_graph_exposes_report_as_one_top_level_node():
    graph = build_application_graph()
    node_names = set(graph.get_graph().nodes)

    assert "report" in node_names
    assert "report_assembly" not in node_names
    assert "report_generation" not in node_names
    assert "report_rendering" not in node_names


def test_report_stage_invokes_report_graph_and_returns_public_fields(monkeypatch):
    report = build_test_report()
    expected_input_keys = {
        "company_research",
        "financial_research",
        "market_research",
        "industry_macro_research",
        "valuation",
        "risk_analysis",
        "investment_decision",
    }

    class FakeReportGraph:
        def invoke(self, payload):
            assert set(payload) == expected_input_keys
            return {
                "report": report,
                "report_assembly_error": "",
                "report_generation_error": "",
                "report_merge_error": "",
                "report_markdown": "# AAPL Investment Research Report",
                "report_rendering_error": "",
            }

    monkeypatch.setattr(application_graph_module, "report_graph", FakeReportGraph())
    result = run_report_stage(
        {
            "ticker": "AAPL",
            "company_research": object(),
            "financial_research": object(),
            "market_research": object(),
            "industry_macro_research": object(),
            "valuation": object(),
            "risk_analysis": object(),
            "investment_decision": object(),
            "stage_errors": {},
        }
    )

    assert isinstance(result["report"], InvestmentReport)
    assert result["report"] is report
    assert result["report_markdown"].startswith("# AAPL")
    assert result["application_error"] == ""
    assert result["current_stage"] == "completed"


def test_report_stage_collects_report_errors_without_losing_report(monkeypatch):
    report = build_test_report()

    class FakeReportGraph:
        def invoke(self, payload):
            return {
                "report": report,
                "report_assembly_error": "",
                "report_generation_error": "LLM unavailable",
                "report_merge_error": "",
                "report_markdown": "# AAPL Investment Research Report",
                "report_rendering_error": "",
            }

    monkeypatch.setattr(application_graph_module, "report_graph", FakeReportGraph())
    result = run_report_stage(
        {
            "ticker": "AAPL",
            "company_research": object(),
            "financial_research": object(),
            "market_research": object(),
            "industry_macro_research": object(),
            "valuation": object(),
            "risk_analysis": object(),
            "investment_decision": object(),
            "stage_errors": {},
        }
    )

    assert result["report"] is report
    assert result["report_markdown"]
    assert result["stage_errors"]["report_generation"] == "LLM unavailable"
    assert "LLM unavailable" in result["application_error"]
    assert result["current_stage"] == "report"


def test_runtime_factory_builds_production_application_graph():
    from langgraph.checkpoint.memory import InMemorySaver

    from app.graph.runtime import create_application_graph

    graph = create_application_graph(checkpointer=InMemorySaver())
    node_names = set(graph.get_graph().nodes)

    assert "report" in node_names
    assert "report_assembly" not in node_names
    assert "report_generation" not in node_names
    assert "report_rendering" not in node_names
