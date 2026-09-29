import pytest

from app.valuation.calculations import calculate_pe_implied_value
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