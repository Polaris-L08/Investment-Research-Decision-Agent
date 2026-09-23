from app.graph.models import ResearchSummary


def test_research_summary_model():
    research = ResearchSummary(
        summary="Strong business fundamentals.",
        key_factors=[
            "Revenue growth",
            "Profitability",
            "Competitive position",
        ],
    )

    assert research.summary == "Strong business fundamentals."

    assert research.key_factors == [
        "Revenue growth",
        "Profitability",
        "Competitive position",
    ]