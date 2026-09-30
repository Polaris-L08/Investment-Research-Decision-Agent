import pytest

from app.valuation.calculations import (
    calculate_expected_upside,
    calculate_pe_implied_value,
    calculate_target_price,
)
from app.valuation.models import ValuationAssumptions, ValuationInputs


def make_inputs(eps: float) -> ValuationInputs:
    return ValuationInputs(earnings_per_share=eps)


def make_assumptions(multiple: float) -> ValuationAssumptions:
    return ValuationAssumptions(
        multiple=multiple,
        rationale="Test valuation multiple.",
    )


def test_calculate_pe_implied_value_with_known_inputs():
    result = calculate_pe_implied_value(
        make_inputs(10.0),
        make_assumptions(20.0),
    )

    assert result == 200.0


def test_calculate_pe_implied_value_preserves_decimal_result():
    result = calculate_pe_implied_value(
        make_inputs(7.5),
        make_assumptions(18.0),
    )

    assert result == 135.0


@pytest.mark.parametrize(
    "eps,multiple,expected",
    [
        (1.0, 10.0, 10.0),
        (12.5, 8.0, 100.0),
        (25.25, 12.0, 303.0),
    ],
)
def test_calculate_pe_implied_value_matches_formula(eps, multiple, expected):
    result = calculate_pe_implied_value(
        make_inputs(eps),
        make_assumptions(multiple),
    )

    assert result == expected


def test_calculate_target_price_uses_implied_value():
    assert calculate_target_price(200.0) == 200.0


def test_calculate_target_price_rejects_non_positive_value():
    with pytest.raises(ValueError, match="Implied value per share must be positive"):
        calculate_target_price(0.0)


@pytest.mark.parametrize(
    "target,current,expected",
    [
        (200.0, 160.0, 0.25),
        (200.0, 200.0, 0.0),
        (160.0, 200.0, -0.20),
    ],
)
def test_calculate_expected_upside_matches_formula(target, current, expected):
    result = calculate_expected_upside(target, current)

    assert result == pytest.approx(expected)


def test_calculate_expected_upside_rejects_non_positive_current_price():
    with pytest.raises(ValueError, match="Current price must be positive"):
        calculate_expected_upside(200.0, 0.0)


def test_calculate_expected_upside_rejects_non_positive_target_price():
    with pytest.raises(ValueError, match="Target price must be positive"):
        calculate_expected_upside(0.0, 200.0)
