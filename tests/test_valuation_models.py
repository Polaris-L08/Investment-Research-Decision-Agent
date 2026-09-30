import pytest
from pydantic import ValidationError

from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)


def make_inputs() -> ValuationInputs:
    return ValuationInputs(earnings_per_share=10.0)


def make_assumptions() -> ValuationAssumptions:
    return ValuationAssumptions(
        multiple=20.0,
        rationale="Selected as the assumed earnings multiple for the model.",
    )


def make_metadata() -> ValuationMetadata:
    return ValuationMetadata(currency="USD", model_version="pe-v1")


def make_result() -> ValuationResult:
    return ValuationResult(
        ticker="AAPL",
        method=ValuationMethod.PE,
        inputs=make_inputs(),
        assumptions=make_assumptions(),
        implied_value_per_share=200.0,
        target_price=200.0,
        current_price=160.0,
        expected_upside=0.25,
        metadata=make_metadata(),
    )


def test_valuation_method_contains_supported_method():
    assert ValuationMethod.PE.value == "P/E"


def test_valuation_inputs_are_structured():
    inputs = make_inputs()
    assert inputs.earnings_per_share == 10.0


def test_valuation_assumptions_are_explicit():
    assumptions = make_assumptions()
    assert assumptions.multiple == 20.0
    assert assumptions.rationale


def test_valuation_result_contains_target_price_and_expected_upside():
    result = make_result()

    assert result.target_price == 200.0
    assert result.current_price == 160.0
    assert result.expected_upside == 0.25


def test_valuation_result_preserves_implied_value():
    result = make_result()
    assert result.implied_value_per_share == 200.0


@pytest.mark.parametrize(
    "field,value",
    [
        ("earnings_per_share", 0),
        ("earnings_per_share", -1),
    ],
)
def test_valuation_inputs_reject_non_positive_values(field, value):
    values = {"earnings_per_share": 10.0}
    values[field] = value

    with pytest.raises(ValidationError):
        ValuationInputs(**values)


def test_valuation_assumptions_reject_non_positive_multiple():
    with pytest.raises(ValidationError):
        ValuationAssumptions(
            multiple=0,
            rationale="Invalid assumption.",
        )


def test_valuation_assumptions_reject_empty_rationale():
    with pytest.raises(ValidationError):
        ValuationAssumptions(
            multiple=20.0,
            rationale="",
        )


def test_valuation_result_rejects_non_positive_implied_value():
    with pytest.raises(ValidationError):
        ValuationResult(
            ticker="AAPL",
            method=ValuationMethod.PE,
            inputs=make_inputs(),
            assumptions=make_assumptions(),
            implied_value_per_share=0,
            target_price=200.0,
            current_price=160.0,
            expected_upside=0.25,
            metadata=make_metadata(),
        )


def test_valuation_result_rejects_non_positive_target_price():
    with pytest.raises(ValidationError):
        ValuationResult(
            ticker="AAPL",
            method=ValuationMethod.PE,
            inputs=make_inputs(),
            assumptions=make_assumptions(),
            implied_value_per_share=200.0,
            target_price=0,
            current_price=160.0,
            expected_upside=0.25,
            metadata=make_metadata(),
        )


def test_valuation_result_rejects_non_positive_current_price():
    with pytest.raises(ValidationError):
        ValuationResult(
            ticker="AAPL",
            method=ValuationMethod.PE,
            inputs=make_inputs(),
            assumptions=make_assumptions(),
            implied_value_per_share=200.0,
            target_price=200.0,
            current_price=0,
            expected_upside=0.25,
            metadata=make_metadata(),
        )


def test_valuation_result_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        ValuationResult(
            ticker="AAPL",
            method=ValuationMethod.PE,
            inputs=make_inputs(),
            assumptions=make_assumptions(),
            implied_value_per_share=200.0,
            target_price=200.0,
            current_price=160.0,
            expected_upside=0.25,
            metadata=make_metadata(),
            unexpected_field="not allowed",
        )
