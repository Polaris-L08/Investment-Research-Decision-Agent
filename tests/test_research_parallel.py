from app.agents.research_parallel import research_parallel_graph
from app.agents.research_state import merge_research_errors


def test_parallel_research_executes_all_agents(monkeypatch):
    executed = []

    def mock_company(state):
        executed.append("company")
        return {
            "company_research": None,
            "research_errors": {},
        }

    def mock_financial(state):
        executed.append("financial")
        return {
            "financial_research": None,
            "research_errors": {},
        }

    def mock_market(state):
        executed.append("market")
        return {
            "market_research": None,
            "research_errors": {},
        }

    def mock_industry_macro(state):
        executed.append("industry_macro")
        return {
            "industry_macro_research": None,
            "research_errors": {},
        }

    monkeypatch.setattr(
        "app.agents.research_parallel.company_research_graph.invoke",
        mock_company,
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.financial_research_graph.invoke",
        mock_financial,
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.market_research_graph.invoke",
        mock_market,
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.industry_macro_research_graph.invoke",
        mock_industry_macro,
    )

    result = research_parallel_graph.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert set(executed) == {
        "company",
        "financial",
        "market",
        "industry_macro",
    }


def test_parallel_research_preserves_all_results(monkeypatch):
    company_result = object()
    financial_result = object()
    market_result = object()
    industry_macro_result = object()

    monkeypatch.setattr(
        "app.agents.research_parallel.company_research_graph.invoke",
        lambda state: {
            "company_research": company_result,
            "research_errors": {},
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.financial_research_graph.invoke",
        lambda state: {
            "financial_research": financial_result,
            "research_errors": {},
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.market_research_graph.invoke",
        lambda state: {
            "market_research": market_result,
            "research_errors": {},
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.industry_macro_research_graph.invoke",
        lambda state: {
            "industry_macro_research": industry_macro_result,
            "research_errors": {},
        },
    )

    result = research_parallel_graph.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert result["company_research"] is company_result
    assert result["financial_research"] is financial_result
    assert result["market_research"] is market_result
    assert (
        result["industry_macro_research"]
        is industry_macro_result
    )


def test_research_errors_reducer_merges_errors():
    existing = {
        "company": "Company research failed.",
    }

    new = {
        "financial": "Financial research failed.",
    }

    merged = merge_research_errors(
        existing,
        new,
    )

    assert merged == {
        "company": "Company research failed.",
        "financial": "Financial research failed.",
    }


def test_parallel_research_merges_errors(monkeypatch):
    monkeypatch.setattr(
        "app.agents.research_parallel.company_research_graph.invoke",
        lambda state: {
            "company_research": None,
            "research_errors": {
                "company": "Company failed.",
            },
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.financial_research_graph.invoke",
        lambda state: {
            "financial_research": None,
            "research_errors": {
                "financial": "Financial failed.",
            },
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.market_research_graph.invoke",
        lambda state: {
            "market_research": None,
            "research_errors": {
                "market": "Market failed.",
            },
        },
    )

    monkeypatch.setattr(
        "app.agents.research_parallel.industry_macro_research_graph.invoke",
        lambda state: {
            "industry_macro_research": None,
            "research_errors": {
                "industry_macro": "Industry/macro failed.",
            },
        },
    )

    result = research_parallel_graph.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert result["research_errors"] == {
        "company": "Company failed.",
        "financial": "Financial failed.",
        "market": "Market failed.",
        "industry_macro": "Industry/macro failed.",
    }