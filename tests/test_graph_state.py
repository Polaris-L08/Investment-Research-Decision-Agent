from app.graph.graph import initialize_state
from app.graph.models import InvestmentHorizon, Recommendation


def test_initialize_state_uses_valid_business_enums():
    state = initialize_state(
        {
            "user_query": "Analyze Apple as a long-term investment",
            "ticker": "AAPL",
        }
    )

    assert state["recommendation"] == Recommendation.HOLD
    assert state["investment_horizon"] == InvestmentHorizon.LONG_TERM