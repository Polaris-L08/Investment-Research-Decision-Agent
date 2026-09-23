from unittest.mock import MagicMock, patch

from app.graph.graph import graph, llm_node, retry_llm, MAX_LLM_RETRIES, investment_decision_node, decision_prompt, \
    prepare_output
from app.graph.models import ResearchSummary, InvestmentDecision, Recommendation, InvestmentHorizon


def test_graph_calls_llm_with_formatted_prompt():
    fake_response = MagicMock()
    fake_response.content = "Mocked investment research response."

    with patch(
        "langchain_openai.ChatOpenAI.invoke",
        return_value=fake_response,
    ) as mock_invoke:

        result = graph.invoke(
            {
                "user_query": "Analyze Apple as a long-term investment",
                "ticker": "AAPL",
            }
        )

    mock_invoke.assert_called_once()

    prompt_value = mock_invoke.call_args.args[0]

    prompt_text = "\n".join(
        message.content
        for message in prompt_value.messages
    )

    assert "AAPL" in prompt_text
    assert "Analyze Apple as a long-term investment" in prompt_text

    assert result["ticker"] == "AAPL"
    assert result["failure_reason"] == ""


def test_llm_node_uses_structured_output():
    fake_response = ResearchSummary(
        summary="Strong business fundamentals.",
        key_factors=[
            "Revenue growth",
            "Profitability",
            "Competitive position",
        ],
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_response

    state = {
        "user_query": "Analyze Apple as a long-term investment",
        "ticker": "AAPL",
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
        "target_price": 0.0,
        "risk_factors": [],
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "investment_thesis": "",
        "llm_response": "",
    }

    with patch(
        "app.graph.graph.structured_llm",
        fake_structured_llm,
    ):
        result = llm_node(state)

    fake_structured_llm.invoke.assert_called_once()

    assert result["llm_response"] == "Strong business fundamentals."


def test_llm_node_writes_structured_output_to_state():
    fake_response = ResearchSummary(
        summary="Strong business fundamentals.",
        key_factors=[
            "Revenue growth",
            "Profitability",
            "Competitive position",
        ],
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_response

    state = {
        "user_query": "Analyze Apple as a long-term investment",
        "ticker": "AAPL",
        "research_plan": [],
        "company_research": "",
        "financial_research": "",
        "market_research": "",
        "industry_research": "",
        "valuation_summary": "",
        "current_price": 0.0,
        "target_price": 0.0,
        "risk_factors": [],
        "recommendation": "Hold",
        "investment_horizon": "Long Term",
        "investment_thesis": "",
        "llm_response": "",
        "research_summary": ResearchSummary(
            summary="",
            key_factors=[],
        ),
    }

    with patch(
        "app.graph.graph.structured_llm",
        fake_structured_llm,
    ):
        result = llm_node(state)

    fake_structured_llm.invoke.assert_called_once()

    assert result["research_summary"] == fake_response
    assert result["research_summary"].summary == (
        "Strong business fundamentals."
    )
    assert result["research_summary"].key_factors == [
        "Revenue growth",
        "Profitability",
        "Competitive position",
    ]


from unittest.mock import MagicMock, patch

from app.graph.graph import graph


def test_graph_routes_to_failure_when_structured_llm_fails():
    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.side_effect = ValueError(
        "Invalid structured output"
    )

    with patch(
        "app.graph.graph.structured_llm",
        fake_structured_llm,
    ):
        result = graph.invoke(
            {
                "user_query": "Analyze Apple as a long-term investment",
                "ticker": "AAPL",
            }
        )

    fake_structured_llm.invoke.assert_called_once()

    assert "failure_reason" in result
    assert "Invalid structured output" in result["failure_reason"]


from app.graph.graph import route_after_llm


def test_route_after_llm_returns_failure_on_error():
    state = {
        "llm_error": "Invalid structured output",
    }

    assert route_after_llm(state) == "llm_failure"


def test_route_after_llm_continues_without_error():
    state = {
        "llm_error": "",
    }

    assert route_after_llm(state) == "continue"


def test_route_after_llm_retries_when_retries_remain():
    state = {
        "llm_error": "Invalid structured output",
        "retry_count": 0,
    }

    assert route_after_llm(state) == "retry"


def test_retry_llm_increments_retry_count_and_clears_error():
    state = {
        "retry_count": 0,
        "llm_error": "Invalid structured output",
    }

    result = retry_llm(state)

    assert result["retry_count"] == 1
    assert result["llm_error"] == ""


from unittest.mock import MagicMock, patch

from app.graph.models import ResearchSummary


def test_graph_retries_after_llm_failure_and_then_succeeds():
    fake_response = ResearchSummary(
        summary="Recovered after retry.",
        key_factors=[
            "Revenue growth",
            "Profitability",
        ],
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.side_effect = [
        ValueError("First attempt failed"),
        fake_response,
    ]

    with patch(
        "app.graph.graph.structured_llm",
        fake_structured_llm,
    ):
        result = graph.invoke(
            {
                "user_query": "Analyze Apple as a long-term investment",
                "ticker": "AAPL",
            }
        )

    assert fake_structured_llm.invoke.call_count == 2

    assert result["ticker"] == "AAPL"
    assert result["failure_reason"] == ""


def test_graph_stops_after_max_llm_retries():
    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.side_effect = ValueError(
        "Persistent structured output failure"
    )

    with patch(
        "app.graph.graph.structured_llm",
        fake_structured_llm,
    ):
        result = graph.invoke(
            {
                "user_query": "Analyze Apple as a long-term investment",
                "ticker": "AAPL",
            }
        )

    assert fake_structured_llm.invoke.call_count == (
        MAX_LLM_RETRIES + 1
    )

    assert result["ticker"] == "AAPL"
    assert result["failure_reason"] != ""
    assert "Persistent structured output failure" in (
        result["failure_reason"]
    )


def test_investment_decision_node_returns_structured_decision():
    fake_decision = InvestmentDecision(
        recommendation=Recommendation.BUY,
        investment_horizon=InvestmentHorizon.LONG_TERM,
        investment_thesis=(
            "Strong business fundamentals support a long-term position."
        ),
    )

    fake_structured_decision_llm = MagicMock()
    fake_structured_decision_llm.invoke.return_value = fake_decision

    state = {
        "user_query": "Analyze Apple as a long-term investment",
        "ticker": "AAPL",
        "research_summary": ResearchSummary(
            summary="Strong business fundamentals.",
            key_factors=[
                "Revenue growth",
                "Profitability",
            ],
        ),
        "llm_error": "",
    }

    with patch(
        "app.graph.graph.structured_decision_llm",
        fake_structured_decision_llm,
    ):
        result = investment_decision_node(state)

    fake_structured_decision_llm.invoke.assert_called_once()

    assert result["investment_decision"] == fake_decision
    assert (
        result["investment_decision"].recommendation
        == Recommendation.BUY
    )
    assert (
        result["investment_decision"].investment_horizon
        == InvestmentHorizon.LONG_TERM
    )


def test_decision_prompt_injects_research_context():
    prompt_value = decision_prompt.invoke(
        {
            "ticker": "AAPL",
            "user_query": "Evaluate Apple as a long-term investment.",
            "research_summary": "Strong business fundamentals.",
            "key_factors": "Revenue growth, Profitability",
        }
    )

    prompt_text = "\n".join(
        message.content
        for message in prompt_value.messages
    )

    assert "AAPL" in prompt_text
    assert "Strong business fundamentals." in prompt_text
    assert "Revenue growth, Profitability" in prompt_text


def test_investment_decision_node_returns_structured_decision():
    fake_decision = InvestmentDecision(
        recommendation=Recommendation.BUY,
        investment_horizon=InvestmentHorizon.LONG_TERM,
        investment_thesis=(
            "Strong business fundamentals support a long-term position."
        ),
    )

    fake_structured_decision_llm = MagicMock()
    fake_structured_decision_llm.invoke.return_value = fake_decision

    state = {
        "user_query": "Analyze Apple as a long-term investment",
        "ticker": "AAPL",
        "research_summary": ResearchSummary(
            summary="Strong business fundamentals.",
            key_factors=[
                "Revenue growth",
                "Profitability",
            ],
        ),
        "llm_error": "",
    }

    with patch(
        "app.graph.graph.structured_decision_llm",
        fake_structured_decision_llm,
    ):
        result = investment_decision_node(state)

    fake_structured_decision_llm.invoke.assert_called_once()

    assert result["investment_decision"] == fake_decision
    assert (
        result["investment_decision"].recommendation
        == Recommendation.BUY
    )
    assert (
        result["investment_decision"].investment_horizon
        == InvestmentHorizon.LONG_TERM
    )


def test_prepare_output_uses_investment_decision():
    state = {
        "ticker": "AAPL",
        "current_price": 200.0,
        "target_price": 250.0,
        "investment_decision": InvestmentDecision(
            recommendation=Recommendation.BUY,
            investment_horizon=InvestmentHorizon.LONG_TERM,
            investment_thesis="Strong long-term fundamentals.",
        ),
        "failure_reason": "",
    }

    result = prepare_output(state)

    assert result["ticker"] == "AAPL"
    assert result["recommendation"] == Recommendation.BUY
    assert result["investment_horizon"] == InvestmentHorizon.LONG_TERM
    assert result["investment_thesis"] == (
        "Strong long-term fundamentals."
    )
    assert result["failure_reason"] == ""


def test_graph_produces_investment_decision_output():
    fake_research = ResearchSummary(
        summary="Strong business fundamentals.",
        key_factors=[
            "Revenue growth",
            "Profitability",
        ],
    )

    fake_decision = InvestmentDecision(
        recommendation=Recommendation.BUY,
        investment_horizon=InvestmentHorizon.LONG_TERM,
        investment_thesis="Strong long-term fundamentals.",
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_research

    fake_structured_decision_llm = MagicMock()
    fake_structured_decision_llm.invoke.return_value = fake_decision

    with (
        patch(
            "app.graph.graph.structured_research_llm",
            fake_structured_llm,
        ),
        patch(
            "app.graph.graph.structured_decision_llm",
            fake_structured_decision_llm,
        ),
    ):
        result = graph.invoke(
            {
                "user_query": "Analyze Apple as a long-term investment",
                "ticker": "AAPL",
            }
        )

    assert result["ticker"] == "AAPL"
    assert result["recommendation"] == Recommendation.BUY
    assert result["investment_horizon"] == (
        InvestmentHorizon.LONG_TERM
    )
    assert result["investment_thesis"] == (
        "Strong long-term fundamentals."
    )
    assert result["failure_reason"] == ""