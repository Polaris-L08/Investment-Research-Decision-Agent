from unittest.mock import MagicMock, patch

from app.agents.models import (
    ResearchArea,
    ResearchPlan,
)
from app.agents.research_planner import (
    research_planner_graph,
)


def test_research_planner_returns_expected_plan():
    result = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
            ResearchArea.FINANCIAL,
            ResearchArea.MARKET,
            ResearchArea.INDUSTRY_MACRO,
        ],
        rationale=(
            "A comprehensive research request requires "
            "all available research areas."
        ),
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = result

    with patch(
        "app.agents.research_planner."
        "structured_research_planner_llm",
        fake_structured_llm,
    ):
        output = research_planner_graph.invoke(
            {
                "user_query": (
                    "Conduct comprehensive research on AAPL."
                )
            }
        )

    assert output["research_plan"] == result
    assert output["research_error"] == ""


def test_research_planner_maps_llm_failure():
    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.side_effect = RuntimeError(
        "Research planner LLM failed."
    )

    with patch(
        "app.agents.research_planner."
        "structured_research_planner_llm",
        fake_structured_llm,
    ):
        output = research_planner_graph.invoke(
            {
                "user_query": "Research AAPL."
            }
        )

    assert output["research_plan"] is None
    assert output["research_error"] == (
        "Research planner LLM failed."
    )


def test_research_planner_accepts_only_user_query():
    result = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
        ],
        rationale="The request asks for basic company information.",
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = result

    with patch(
        "app.agents.research_planner."
        "structured_research_planner_llm",
        fake_structured_llm,
    ):
        output = research_planner_graph.invoke(
            {
                "user_query": "Give me basic information about AAPL."
            }
        )

    assert output["research_plan"].research_areas == [
        ResearchArea.COMPANY
    ]