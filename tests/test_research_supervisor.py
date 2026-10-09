from __future__ import annotations

from typing import Any, Callable

import pytest

import app.agents.research_supervisor as supervisor
from app.agents.models import ResearchArea, ResearchPlan


USER_QUERY = "Analyze Apple's business and financial outlook."


class FakeGraph:
    """A minimal graph double that records invoke calls."""

    def __init__(
        self,
        handler: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        self.handler = handler
        self.calls: list[dict[str, Any]] = []

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(state)
        return self.handler(state)


def make_plan(*areas: ResearchArea) -> ResearchPlan:
    return ResearchPlan(
        research_areas=list(areas),
        rationale="The requested research areas are relevant to the analysis.",
    )


def install_fake_graphs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    planner_handler: Callable[
        [dict[str, Any]], dict[str, Any]
    ],
    child_handlers: dict[
        ResearchArea,
        Callable[[dict[str, Any]], dict[str, Any]],
    ] | None = None,
):
    """Replace module-level graph references used by Supervisor nodes."""

    planner = FakeGraph(planner_handler)
    monkeypatch.setattr(
        supervisor,
        "research_planner_graph",
        planner,
    )

    child_handlers = child_handlers or {}

    graph_names = {
        ResearchArea.COMPANY: "company_research_graph",
        ResearchArea.FINANCIAL: "financial_research_graph",
        ResearchArea.MARKET: "market_research_graph",
        ResearchArea.INDUSTRY_MACRO: "industry_macro_research_graph",
    }

    child_graphs: dict[ResearchArea, FakeGraph] = {}

    for area, attribute_name in graph_names.items():

        def default_handler(
            state: dict[str, Any],
            *,
            current_area: ResearchArea = area,
        ) -> dict[str, Any]:
            return {
                "research_result": {
                    "area": current_area.value,
                    "ticker": state["ticker"],
                },
                "research_error": "",
            }

        handler = child_handlers.get(area, default_handler)
        fake_graph = FakeGraph(handler)

        monkeypatch.setattr(
            supervisor,
            attribute_name,
            fake_graph,
        )
        child_graphs[area] = fake_graph

    return planner, child_graphs


def planner_returns(plan: ResearchPlan):
    def handler(state: dict[str, Any]) -> dict[str, Any]:
        return {
            "research_plan": plan,
            "planning_error": "",
        }

    return handler


def valid_input(
    *,
    ticker: str = "AAPL",
    user_query: str = USER_QUERY,
) -> dict[str, str]:
    return {
        "ticker": ticker,
        "user_query": user_query,
    }


def test_supervisor_executes_all_planned_areas_in_order(
    monkeypatch: pytest.MonkeyPatch,
):
    plan = make_plan(
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
        ResearchArea.INDUSTRY_MACRO,
    )

    execution_order: list[ResearchArea] = []

    child_handlers = {}

    for area in plan.research_areas:

        def handler(
            state: dict[str, Any],
            *,
            current_area: ResearchArea = area,
        ) -> dict[str, Any]:
            execution_order.append(current_area)
            return {
                "research_result": {
                    "area": current_area.value,
                    "ticker": state["ticker"],
                },
                "research_error": "",
            }

        child_handlers[area] = handler

    planner, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_returns(plan),
        child_handlers=child_handlers,
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    assert planner.calls == [
        {"user_query": USER_QUERY},
    ]

    assert execution_order == plan.research_areas

    assert result["completed_research_areas"] == plan.research_areas
    assert result["research_plan"] == plan
    assert result["ticker"] == "AAPL"

    assert result["company_research"] == {
        "area": ResearchArea.COMPANY.value,
        "ticker": "AAPL",
    }
    assert result["financial_research"] == {
        "area": ResearchArea.FINANCIAL.value,
        "ticker": "AAPL",
    }
    assert result["market_research"] == {
        "area": ResearchArea.MARKET.value,
        "ticker": "AAPL",
    }
    assert result["industry_macro_research"] == {
        "area": ResearchArea.INDUSTRY_MACRO.value,
        "ticker": "AAPL",
    }

    for area in plan.research_areas:
        assert child_graphs[area].calls == [
            {"ticker": "AAPL"},
        ]

    # Internal orchestration fields must not leak into the public output.
    assert "user_query" not in result
    assert "next_research_area" not in result


def test_supervisor_respects_partial_plan_and_requested_order(
    monkeypatch: pytest.MonkeyPatch,
):
    plan = make_plan(
        ResearchArea.MARKET,
        ResearchArea.COMPANY,
    )

    execution_order: list[ResearchArea] = []
    child_handlers = {}

    for area in plan.research_areas:

        def handler(
            state: dict[str, Any],
            *,
            current_area: ResearchArea = area,
        ) -> dict[str, Any]:
            execution_order.append(current_area)
            return {
                "research_result": current_area.value,
                "research_error": "",
            }

        child_handlers[area] = handler

    _, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_returns(plan),
        child_handlers=child_handlers,
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    assert execution_order == [
        ResearchArea.MARKET,
        ResearchArea.COMPANY,
    ]

    assert result["completed_research_areas"] == [
        ResearchArea.MARKET,
        ResearchArea.COMPANY,
    ]

    assert result["market_research"] == ResearchArea.MARKET.value
    assert result["company_research"] == ResearchArea.COMPANY.value

    assert child_graphs[ResearchArea.FINANCIAL].calls == []
    assert child_graphs[ResearchArea.INDUSTRY_MACRO].calls == []

    assert "financial_research" not in result
    assert "industry_macro_research" not in result


def test_supervisor_passes_user_query_to_planner(
    monkeypatch: pytest.MonkeyPatch,
):
    plan = make_plan(ResearchArea.COMPANY)
    planner, _ = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_returns(plan),
    )

    query = "  Assess Apple's competitive position.  "

    supervisor.research_supervisor_graph.invoke(
        valid_input(user_query=query)
    )

    assert planner.calls == [
        {"user_query": query.strip()},
    ]


def test_child_error_is_recorded_and_later_areas_still_execute(
    monkeypatch: pytest.MonkeyPatch,
):
    plan = make_plan(
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
    )

    execution_order: list[ResearchArea] = []

    def company_fails(state: dict[str, Any]) -> dict[str, Any]:
        execution_order.append(ResearchArea.COMPANY)
        return {
            "research_result": None,
            "research_error": "Company data provider timed out.",
        }

    def financial_succeeds(state: dict[str, Any]) -> dict[str, Any]:
        execution_order.append(ResearchArea.FINANCIAL)
        return {
            "research_result": {"summary": "Financial analysis completed."},
            "research_error": "",
        }

    def market_succeeds(state: dict[str, Any]) -> dict[str, Any]:
        execution_order.append(ResearchArea.MARKET)
        return {
            "research_result": {"summary": "Market analysis completed."},
            "research_error": "",
        }

    _, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_returns(plan),
        child_handlers={
            ResearchArea.COMPANY: company_fails,
            ResearchArea.FINANCIAL: financial_succeeds,
            ResearchArea.MARKET: market_succeeds,
        },
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    assert execution_order == plan.research_areas

    assert result["completed_research_areas"] == plan.research_areas

    assert result["research_errors"] == {
        ResearchArea.COMPANY.value:
            "Company data provider timed out.",
    }

    assert result["company_research"] is None
    assert result["financial_research"] == {
        "summary": "Financial analysis completed.",
    }
    assert result["market_research"] == {
        "summary": "Market analysis completed.",
    }

    # A child error must not prevent subsequent child graphs from running.
    assert len(child_graphs[ResearchArea.FINANCIAL].calls) == 1
    assert len(child_graphs[ResearchArea.MARKET].calls) == 1


def test_child_exception_is_converted_to_research_error(
    monkeypatch: pytest.MonkeyPatch,
):
    plan = make_plan(
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
    )

    def company_raises(state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("simulated child graph crash")

    def financial_succeeds(state: dict[str, Any]) -> dict[str, Any]:
        return {
            "research_result": {"summary": "Financial research succeeded."},
            "research_error": "",
        }

    _, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_returns(plan),
        child_handlers={
            ResearchArea.COMPANY: company_raises,
            ResearchArea.FINANCIAL: financial_succeeds,
        },
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    assert result["research_errors"] == {
        ResearchArea.COMPANY.value:
            "Child research graph invocation failed: simulated child graph crash",
    }

    assert result["completed_research_areas"] == plan.research_areas

    assert result["financial_research"] == {
        "summary": "Financial research succeeded.",
    }

    assert len(child_graphs[ResearchArea.FINANCIAL].calls) == 1


def test_planner_error_stops_child_execution(
    monkeypatch: pytest.MonkeyPatch,
):
    planner, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=lambda state: {
            "research_plan": None,
            "planning_error": "Unable to create a valid research plan.",
        },
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    assert len(planner.calls) == 1

    assert result["research_plan"] is None
    assert result["planning_error"] == (
        "Unable to create a valid research plan."
    )
    assert result["supervisor_error"] == (
        "Unable to create a valid research plan."
    )

    assert all(
        graph.calls == []
        for graph in child_graphs.values()
    )


def test_planner_exception_stops_child_execution(
    monkeypatch: pytest.MonkeyPatch,
):
    def planner_raises(state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("simulated planner crash")

    planner, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_raises,
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    assert len(planner.calls) == 1

    assert result["research_plan"] is None
    assert result["planning_error"] == (
        "Research planner invocation failed: simulated planner crash"
    )
    assert result["supervisor_error"] == (
        "Research planner invocation failed: simulated planner crash"
    )

    assert all(
        graph.calls == []
        for graph in child_graphs.values()
    )


@pytest.mark.parametrize(
    ("ticker", "user_query", "expected_error_field"),
    [
        ("", USER_QUERY, "supervisor_error"),
        ("   ", USER_QUERY, "supervisor_error"),
        ("AAPL", "", "planning_error"),
        ("AAPL", "   ", "planning_error"),
    ],
)
def test_invalid_input_stops_before_planner_or_child_execution(
    monkeypatch: pytest.MonkeyPatch,
    ticker: str,
    user_query: str,
    expected_error_field: str,
):
    planner, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_returns(
            make_plan(ResearchArea.COMPANY)
        ),
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input(
            ticker=ticker,
            user_query=user_query,
        )
    )

    assert result[expected_error_field]

    assert planner.calls == []

    assert all(
        graph.calls == []
        for graph in child_graphs.values()
    )


def test_planner_returning_no_plan_stops_execution(
    monkeypatch: pytest.MonkeyPatch,
):
    planner, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=lambda state: {
            "research_plan": None,
            "planning_error": "",
        },
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    assert len(planner.calls) == 1
    assert result["research_plan"] is None
    assert result["planning_error"] == (
        "Research planner returned no plan."
    )
    assert result["supervisor_error"] == (
        "Research planner returned no plan."
    )

    assert all(
        graph.calls == []
        for graph in child_graphs.values()
    )


def test_empty_plan_finishes_without_running_child_graphs(
    monkeypatch: pytest.MonkeyPatch,
):
    plan = make_plan()

    _, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_returns(plan),
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    assert result["research_plan"] == plan
    # assert result["completed_research_areas"] == []

    assert all(
        graph.calls == []
        for graph in child_graphs.values()
    )


def test_output_contract_excludes_internal_state_fields(
    monkeypatch: pytest.MonkeyPatch,
):
    plan = make_plan(ResearchArea.COMPANY)

    _, _ = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_returns(plan),
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    expected_public_fields = {
        "ticker",
        "research_plan",
        "completed_research_areas",
        "company_research",
        "financial_research",
        "market_research",
        "industry_macro_research",
        "research_errors",
        "planning_error",
        "supervisor_error",
    }

    assert set(result).issubset(expected_public_fields)

    assert result["ticker"] == "AAPL"
    assert result["research_plan"] == plan
    assert result["completed_research_areas"] == [
        ResearchArea.COMPANY,
    ]

    assert "user_query" not in result
    assert "next_research_area" not in result



@pytest.mark.parametrize(
    "invalid_output",
    [
        None,
        {},
        {"research_result": {"summary": "Missing error key."}},
        {"research_error": "Missing result key."},
        {"research_result": None, "research_error": "   "},
        {
            "research_result": {"summary": "Ambiguous response."},
            "research_error": "The child also reported an error.",
        },
        {"research_result": None, "research_error": 123},
    ],
)
def test_invalid_child_output_contract_stops_research_stage(
    monkeypatch: pytest.MonkeyPatch,
    invalid_output: Any,
):
    plan = make_plan(
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
    )

    _, child_graphs = install_fake_graphs(
        monkeypatch,
        planner_handler=planner_returns(plan),
        child_handlers={
            ResearchArea.COMPANY: lambda state: invalid_output,
        },
    )

    result = supervisor.research_supervisor_graph.invoke(
        valid_input()
    )

    assert result["supervisor_error"].startswith(
        "Invalid output from company research graph:"
    )

    assert child_graphs[ResearchArea.COMPANY].calls == [
        {"ticker": "AAPL"},
    ]

    # The contract error must prevent the next planned child from running.
    assert child_graphs[ResearchArea.FINANCIAL].calls == []

    # A contract error must not be recorded as a completed research area.
    assert result.get("completed_research_areas", []) == []