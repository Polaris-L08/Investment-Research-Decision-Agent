from unittest.mock import MagicMock, patch

import pytest

from app.investment.models import (
    InvestmentConviction,
    InvestmentDecision,
    InvestmentHorizon,
    InvestmentRecommendation,
)
from app.report.generation import (
    EXPECTED_REPORT_SECTION_IDS,
    ReportNarrativeOutput,
    ReportSection,
    ReportSectionId,
    generate_report_narrative,
    merge_report_narrative,
    merge_report_narrative_node,
    report_generation_graph,
)
from app.report.models import InvestmentReport
from app.risk.models import RiskAnalysis
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)


def build_test_report() -> InvestmentReport:
    valuation = ValuationResult(
        ticker="AAPL",
        method=ValuationMethod.PE,
        inputs=ValuationInputs(
            earnings_per_share=7.0,
        ),
        assumptions=ValuationAssumptions(
            multiple=30.0,
            rationale="Stable growth and strong competitive position.",
        ),
        implied_value_per_share=210.0,
        target_price=210.0,
        current_price=180.0,
        expected_upside=(210.0 - 180.0) / 180.0,
        metadata=ValuationMetadata(
            currency="USD",
            model_version="v1.0",
        ),
    )

    risk_analysis = RiskAnalysis(
        ticker="AAPL",
        risks=[],
        overall_risk_level="Medium",
        key_risks=[
            "Competitive pressure",
            "Regulatory uncertainty",
        ],
        uncertainty_notes=["Macro conditions remain uncertain."],
    )

    investment_decision = InvestmentDecision(
        ticker="AAPL",
        recommendation=InvestmentRecommendation.BUY,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        current_price=180.0,
        target_price=210.0,
        expected_upside=(210.0 - 180.0) / 180.0,
        conviction=InvestmentConviction.MEDIUM,
        investment_thesis=(
            "Strong fundamentals and attractive valuation "
            "support a medium-term Buy recommendation."
        ),
        key_catalysts=[
            "Earnings growth",
            "Product expansion",
        ],
        key_risks=[
            "Competitive pressure",
            "Regulatory uncertainty",
        ],
        invalidation_conditions=[
            "Material deterioration in earnings growth",
        ],
        supporting_evidence=[
            "Healthy earnings profile",
            "Attractive valuation",
        ],
    )

    return InvestmentReport(
        ticker="AAPL",
        title="Investment Research Report - AAPL",
        executive_summary="Original executive summary.",
        company_overview="Original company overview.",
        financial_summary="Original financial summary.",
        market_summary="Original market summary.",
        industry_macro_summary="Original industry and macro summary.",
        valuation_summary="Original valuation summary.",
        risk_summary="Original risk summary.",
        investment_decision_summary="Original investment decision summary.",
        valuation=valuation,
        risk_analysis=risk_analysis,
        investment_decision=investment_decision,
    )


def build_complete_narrative() -> ReportNarrativeOutput:
    return ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=ReportSectionId.EXECUTIVE_SUMMARY,
                content="Generated executive summary.",
            ),
            ReportSection(
                section_id=ReportSectionId.COMPANY_OVERVIEW,
                content="Generated company overview.",
            ),
            ReportSection(
                section_id=ReportSectionId.FINANCIAL_SUMMARY,
                content="Generated financial summary.",
            ),
            ReportSection(
                section_id=ReportSectionId.MARKET_SUMMARY,
                content="Generated market summary.",
            ),
            ReportSection(
                section_id=ReportSectionId.INDUSTRY_MACRO_SUMMARY,
                content="Generated industry and macro summary.",
            ),
            ReportSection(
                section_id=ReportSectionId.VALUATION_SUMMARY,
                content="Generated valuation summary.",
            ),
            ReportSection(
                section_id=ReportSectionId.RISK_SUMMARY,
                content="Generated risk summary.",
            ),
            ReportSection(
                section_id=ReportSectionId.INVESTMENT_DECISION_SUMMARY,
                content="Generated investment decision summary.",
            ),
        ]
    )


def test_merge_report_narrative_returns_completed_report():
    report = build_test_report()
    narrative = build_complete_narrative()

    merged_report = merge_report_narrative(
        report,
        narrative,
    )

    assert isinstance(merged_report, InvestmentReport)

    assert merged_report.executive_summary == (
        "Generated executive summary."
    )
    assert merged_report.company_overview == (
        "Generated company overview."
    )
    assert merged_report.financial_summary == (
        "Generated financial summary."
    )
    assert merged_report.market_summary == (
        "Generated market summary."
    )
    assert merged_report.industry_macro_summary == (
        "Generated industry and macro summary."
    )
    assert merged_report.valuation_summary == (
        "Generated valuation summary."
    )
    assert merged_report.risk_summary == (
        "Generated risk summary."
    )
    assert merged_report.investment_decision_summary == (
        "Generated investment decision summary."
    )


def test_merge_report_narrative_preserves_source_of_truth_objects():
    report = build_test_report()
    narrative = build_complete_narrative()

    merged_report = merge_report_narrative(
        report,
        narrative,
    )

    assert merged_report.valuation == report.valuation
    assert merged_report.risk_analysis == report.risk_analysis
    assert (
        merged_report.investment_decision
        == report.investment_decision
    )


def test_merge_report_narrative_preserves_critical_investment_facts():
    report = build_test_report()
    narrative = build_complete_narrative()

    merged_report = merge_report_narrative(
        report,
        narrative,
    )

    assert merged_report.ticker == report.ticker

    assert (
        merged_report.valuation.current_price
        == report.valuation.current_price
    )
    assert (
        merged_report.valuation.target_price
        == report.valuation.target_price
    )
    assert (
        merged_report.valuation.expected_upside
        == report.valuation.expected_upside
    )

    assert (
        merged_report.investment_decision.recommendation
        == report.investment_decision.recommendation
    )
    assert (
        merged_report.investment_decision.investment_horizon
        == report.investment_decision.investment_horizon
    )
    assert (
        merged_report.investment_decision.conviction
        == report.investment_decision.conviction
    )
    assert (
        merged_report.investment_decision.key_risks
        == report.investment_decision.key_risks
    )


def test_merge_report_narrative_does_not_mutate_original_report():
    report = build_test_report()
    original_report = report.model_copy(deep=True)

    narrative = build_complete_narrative()

    merged_report = merge_report_narrative(
        report,
        narrative,
    )

    assert report == original_report

    assert (
        merged_report.executive_summary
        != report.executive_summary
    )


def test_merge_report_narrative_rejects_incomplete_narrative():
    report = build_test_report()

    narrative = ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=ReportSectionId.EXECUTIVE_SUMMARY,
                content="Only one section.",
            )
        ]
    )

    with pytest.raises(ValueError, match="exactly"):
        merge_report_narrative(
            report,
            narrative,
        )


def test_merge_report_narrative_rejects_duplicate_sections():
    report = build_test_report()

    sections = list(build_complete_narrative().sections)

    sections[-1] = ReportSection(
        section_id=ReportSectionId.EXECUTIVE_SUMMARY,
        content="Duplicate executive summary.",
    )

    narrative = ReportNarrativeOutput(
        sections=sections,
    )

    with pytest.raises(ValueError, match="duplicate"):
        merge_report_narrative(
            report,
            narrative,
        )


def test_merge_report_narrative_rejects_invalid_section_order():
    report = build_test_report()

    sections = list(build_complete_narrative().sections)

    sections[0], sections[1] = sections[1], sections[0]

    narrative = ReportNarrativeOutput(
        sections=sections,
    )

    with pytest.raises(ValueError, match="invalid order"):
        merge_report_narrative(
            report,
            narrative,
        )


def test_merge_report_narrative_node_returns_merge_error_when_report_missing():
    narrative = build_complete_narrative()

    state = {
        "narrative": narrative,
    }

    result = merge_report_narrative_node(state)

    assert result["merge_error"] == (
        "Report is required for narrative merge."
    )


def test_merge_report_narrative_node_returns_merge_error_when_narrative_missing():
    report = build_test_report()

    state = {
        "report": report,
    }

    result = merge_report_narrative_node(state)

    assert result["merge_error"] == (
        "Narrative is required for report merge."
    )


def test_merge_report_narrative_node_returns_completed_report():
    report = build_test_report()
    narrative = build_complete_narrative()

    state = {
        "report": report,
        "narrative": narrative,
    }

    result = merge_report_narrative_node(state)

    assert result["merge_error"] is None
    assert isinstance(result["report"], InvestmentReport)

    assert result["report"].executive_summary == (
        "Generated executive summary."
    )


def test_merge_report_narrative_node_catches_merge_failure():
    report = build_test_report()

    invalid_narrative = ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=ReportSectionId.EXECUTIVE_SUMMARY,
                content="Invalid incomplete narrative.",
            )
        ]
    )

    state = {
        "report": report,
        "narrative": invalid_narrative,
    }

    result = merge_report_narrative_node(state)

    assert "report" not in result
    assert result["merge_error"] is not None


def test_generate_report_narrative_success():
    report = build_test_report()
    expected_narrative = build_complete_narrative()

    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = expected_narrative

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = (
        mock_structured_llm
    )

    state = {
        "report": report,
    }

    with patch(
        "app.report.generation.llm",
        mock_llm,
    ):
        result = generate_report_narrative(state)

    assert result["generation_error"] is None
    assert result["narrative"] == expected_narrative

    mock_llm.with_structured_output.assert_called_once_with(
        ReportNarrativeOutput
    )

    mock_structured_llm.invoke.assert_called_once()


def test_generate_report_narrative_failure_returns_generation_error():
    report = build_test_report()

    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.side_effect = RuntimeError(
        "LLM generation failed."
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = (
        mock_structured_llm
    )

    state = {
        "report": report,
    }

    with patch(
        "app.report.generation.llm",
        mock_llm,
    ):
        result = generate_report_narrative(state)

    assert result["narrative"] is None
    assert result["generation_error"] == (
        "LLM generation failed."
    )


def test_report_generation_graph_success():
    report = build_test_report()
    narrative = build_complete_narrative()

    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = narrative

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = (
        mock_structured_llm
    )

    with patch(
        "app.report.generation.llm",
        mock_llm,
    ):
        result = report_generation_graph.invoke(
            {
                "report": report,
            }
        )

    assert result["generation_error"] is None
    assert result["merge_error"] is None

    assert isinstance(
        result["report"],
        InvestmentReport,
    )

    assert result["report"].executive_summary == (
        "Generated executive summary."
    )

    assert result["report"].investment_decision == (
        report.investment_decision
    )


def test_report_generation_graph_stops_when_generation_fails():
    report = build_test_report()

    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.side_effect = RuntimeError(
        "LLM unavailable."
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = (
        mock_structured_llm
    )

    with patch(
        "app.report.generation.llm",
        mock_llm,
    ):
        result = report_generation_graph.invoke(
            {
                "report": report,
            }
        )

    assert result["generation_error"] == (
        "LLM unavailable."
    )

    assert result["narrative"] is None

    assert result["report"] == report

    assert "merge_error" not in result


def test_report_generation_graph_stops_before_merge_when_narrative_invalid():
    report = build_test_report()

    invalid_narrative = ReportNarrativeOutput(
        sections=[
            ReportSection(
                section_id=ReportSectionId.EXECUTIVE_SUMMARY,
                content="Incomplete narrative.",
            )
        ]
    )

    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = invalid_narrative

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = (
        mock_structured_llm
    )

    with patch(
        "app.report.generation.llm",
        mock_llm,
    ):
        result = report_generation_graph.invoke(
            {
                "report": report,
            }
        )

    assert result["narrative"] is None
    assert result["generation_error"] is not None

    assert result["report"] == report
    assert "merge_error" not in result
