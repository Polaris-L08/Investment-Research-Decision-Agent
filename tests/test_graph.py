from unittest.mock import MagicMock, patch

from app.graph.graph import graph, llm_node
from app.graph.models import ResearchSummary


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