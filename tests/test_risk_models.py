import pytest
from pydantic import ValidationError

from app.risk.models import (
    RiskAnalysis,
    RiskCategory,
    RiskImpact,
    RiskItem,
    RiskLikelihood,
    RiskSeverity,
)


def make_risk_item() -> RiskItem:
    return RiskItem(
        category=RiskCategory.VALUATION,
        title="Valuation Multiple Compression",
        description=(
            "A contraction in the valuation multiple could reduce "
            "the expected return even if operating performance remains strong."
        ),
        severity=RiskSeverity.HIGH,
        likelihood=RiskLikelihood.MEDIUM,
        impact=RiskImpact.HIGH,
        evidence=[
            "The valuation depends on the assumed earnings multiple.",
        ],
    )


def make_risk_analysis() -> RiskAnalysis:
    return RiskAnalysis(
        ticker="NVDA",
        risks=[make_risk_item()],
        overall_risk_level=RiskSeverity.HIGH,
        key_risks=["Valuation Multiple Compression"],
        uncertainty_notes=[
            "The assumed valuation multiple is sensitive to market sentiment."
        ],
    )


def test_risk_category_contains_expected_categories():
    assert RiskCategory.COMPANY.value == "Company"
    assert RiskCategory.OPERATIONAL.value == "Operational"
    assert RiskCategory.FINANCIAL.value == "Financial"
    assert RiskCategory.MARKET.value == "Market"
    assert RiskCategory.VALUATION.value == "Valuation"
    assert RiskCategory.INDUSTRY.value == "Industry"
    assert RiskCategory.MACRO.value == "Macro"
    assert RiskCategory.REGULATORY.value == "Regulatory"
    assert RiskCategory.DATA_UNCERTAINTY.value == "Data Uncertainty"


def test_risk_severity_is_structured():
    assert RiskSeverity.LOW.value == "Low"
    assert RiskSeverity.MEDIUM.value == "Medium"
    assert RiskSeverity.HIGH.value == "High"
    assert RiskSeverity.CRITICAL.value == "Critical"


def test_risk_item_is_structured():
    risk = make_risk_item()

    assert risk.category == RiskCategory.VALUATION
    assert risk.title == "Valuation Multiple Compression"
    assert risk.severity == RiskSeverity.HIGH
    assert risk.likelihood == RiskLikelihood.MEDIUM
    assert risk.impact == RiskImpact.HIGH
    assert risk.evidence


def test_risk_analysis_is_structured():
    analysis = make_risk_analysis()

    assert analysis.ticker == "NVDA"
    assert len(analysis.risks) == 1
    assert analysis.overall_risk_level == RiskSeverity.HIGH
    assert analysis.key_risks == ["Valuation Multiple Compression"]
    assert analysis.uncertainty_notes


def test_risk_item_rejects_empty_title():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_empty_description():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_empty_evidence():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=[],
        )


def test_risk_item_rejects_invalid_category():
    with pytest.raises(ValidationError):
        RiskItem(
            category="Invalid Category",
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity="Extreme",
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_invalid_likelihood():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood="Almost Certain",
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_invalid_impact():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact="Extreme",
            evidence=["Supporting evidence."],
        )


def test_risk_item_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RiskItem(
            category=RiskCategory.COMPANY,
            title="Competitive Risk",
            description="A valid risk description.",
            severity=RiskSeverity.MEDIUM,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.MEDIUM,
            evidence=["Supporting evidence."],
            unexpected_field="not allowed",
        )


def test_risk_analysis_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RiskAnalysis(
            ticker="NVDA",
            risks=[make_risk_item()],
            overall_risk_level=RiskSeverity.HIGH,
            key_risks=["Valuation Multiple Compression"],
            uncertainty_notes=[],
            unexpected_field="not allowed",
        )


def test_risk_analysis_requires_ticker():
    with pytest.raises(ValidationError):
        RiskAnalysis(
            ticker="",
            risks=[make_risk_item()],
            overall_risk_level=RiskSeverity.HIGH,
            key_risks=["Valuation Multiple Compression"],
            uncertainty_notes=[],
        )