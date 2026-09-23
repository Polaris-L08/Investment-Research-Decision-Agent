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