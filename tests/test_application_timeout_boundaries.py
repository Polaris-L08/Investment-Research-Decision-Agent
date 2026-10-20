"""Cancellation must propagate through production Application stage wrappers."""

import asyncio

import pytest

import app.application.graph as application_graph_module
from app.valuation.models import ValuationAssumptions, ValuationInputs


@pytest.mark.parametrize(
    ("graph_attribute", "stage_function"),
    [
        ("research_supervisor_graph", "run_research_stage"),
        ("valuation_graph", "run_valuation_stage"),
        ("risk_graph", "run_risk_stage"),
        ("investment_decision_graph", "run_decision_stage"),
        ("report_graph", "run_report_stage"),
    ],
)
def test_application_stage_does_not_convert_cancellation_to_failure(
    monkeypatch, graph_attribute, stage_function
):
    class CancelledGraph:
        def invoke(self, payload):
            raise asyncio.CancelledError()

    monkeypatch.setattr(application_graph_module, graph_attribute, CancelledGraph())
    state = {
        "ticker": "AAPL",
        "user_query": "Research Apple",
        "memory_context": "",
        "company_research": None,
        "financial_research": None,
        "market_research": None,
        "industry_macro_research": None,
        "valuation": None,
        "valuation_inputs": ValuationInputs(earnings_per_share=1.0),
        "valuation_assumptions": ValuationAssumptions(multiple=10.0, rationale="test assumption"),
        "risk_analysis": None,
        "investment_decision": None,
        "stage_errors": {},
        "error_details": [],
        "application_error": "",
    }

    with pytest.raises(asyncio.CancelledError):
        getattr(application_graph_module, stage_function)(state)
