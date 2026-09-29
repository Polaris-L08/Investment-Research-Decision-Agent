from app.agents.models import ResearchArea, ResearchPlan
from app.agents.research_fanout import research_fanout_graph


def test_fanout_executes_only_selected_research_areas(
    monkeypatch,
):
    executed = []

    monkeypatch.setattr(
        "app.agents.research_fanout.company_research_graph.invoke",
        lambda state: (
            executed.append(ResearchArea.COMPANY)
            or {
                "company_research": None,
                "research_errors": {},
            }
        ),
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.financial_research_graph.invoke",
        lambda state: (
            executed.append(ResearchArea.FINANCIAL)
            or {
                "financial_research": None,
                "research_errors": {},
            }
        ),
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.market_research_graph.invoke",
        lambda state: (
            executed.append(ResearchArea.MARKET)
            or {
                "market_research": None,
                "research_errors": {},
            }
        ),
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.industry_macro_research_graph.invoke",
        lambda state: (
            executed.append(ResearchArea.INDUSTRY_MACRO)
            or {
                "industry_macro_research": None,
                "research_errors": {},
            }
        ),
    )

    plan = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
            ResearchArea.MARKET,
        ],
        rationale="Only company and market research are required.",
    )

    research_fanout_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": plan,
        }
    )

    assert set(executed) == {
        ResearchArea.COMPANY,
        ResearchArea.MARKET,
    }


def test_fanout_respects_research_plan(
    monkeypatch,
):
    executed = []

    def mock_company(state):
        executed.append(ResearchArea.COMPANY)
        return {
            "company_research": None,
            "research_errors": {},
        }

    def mock_financial(state):
        executed.append(ResearchArea.FINANCIAL)
        return {
            "financial_research": None,
            "research_errors": {},
        }

    monkeypatch.setattr(
        "app.agents.research_fanout.company_research_graph.invoke",
        mock_company,
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.financial_research_graph.invoke",
        mock_financial,
    )

    plan = ResearchPlan(
        research_areas=[
            ResearchArea.FINANCIAL,
        ],
        rationale="Financial research is sufficient.",
    )

    research_fanout_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": plan,
        }
    )

    assert executed == [
        ResearchArea.FINANCIAL,
    ]


def test_fanout_merges_research_errors(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.agents.research_fanout.company_research_graph.invoke",
        lambda state: {
            "company_research": None,
            "research_errors": {
                "company": "Company failed.",
            },
        },
    )

    monkeypatch.setattr(
        "app.agents.research_fanout.market_research_graph.invoke",
        lambda state: {
            "market_research": None,
            "research_errors": {
                "market": "Market failed.",
            },
        },
    )

    plan = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
            ResearchArea.MARKET,
        ],
        rationale="Company and market research are required.",
    )

    result = research_fanout_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": plan,
        }
    )

    assert result["research_errors"] == {
        "company": "Company failed.",
        "market": "Market failed.",
    }