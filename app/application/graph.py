"""Production top-level Application Graph.

The graph orchestrates existing domain graphs in this order:
Research -> Valuation -> Risk -> Investment Decision -> Report assembly ->
Report narrative generation. Domain logic remains in its owning modules.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.agents.research_supervisor import research_supervisor_graph
from app.agents.valuation import valuation_graph
from app.agents.risk import build_risk_graph
from app.agents.investment_decision import build_investment_decision_graph
from app.application.contracts import (
    StageContractError,
    normalize_stage_output,
    normalize_valuation_output,
    validate_ticker_consistency,
)
from app.application.state import (
    ApplicationInputState,
    ApplicationOutputState,
    ApplicationState,
)
from app.investment.models import InvestmentDecision
from app.report.assembly import build_investment_report
from app.report.models import InvestmentReport
from app.report.generation import report_generation_graph
from app.risk.models import RiskAnalysis
from app.valuation.models import ValuationResult


_REQUIRED_RESEARCH_FIELDS = (
    "company_research",
    "financial_research",
    "market_research",
    "industry_macro_research",
)


def _stage_errors(state: Mapping[str, Any], stage: str, message: str) -> dict[str, str]:
    errors = dict(state.get("stage_errors") or {})
    errors[stage] = message
    return errors


def _failure_update(
    state: Mapping[str, Any],
    *,
    stage: str,
    message: str,
    result_key: str | None = None,
    error_key: str | None = None,
) -> dict[str, Any]:
    update: dict[str, Any] = {
        "current_stage": stage,
        "stage_errors": _stage_errors(state, stage, message),
        "application_error": f"{stage} failed: {message}",
    }
    if result_key:
        update[result_key] = None
    if error_key:
        update[error_key] = message
    return update


def validate_application_input(state: ApplicationState) -> dict[str, Any]:
    """Validate the public request, without requiring valuation-stage inputs."""
    ticker = state.get("ticker", "")
    user_query = state.get("user_query", "")
    if not isinstance(ticker, str) or not ticker.strip():
        return _failure_update(
            state, stage="input", message="Ticker must be a non-empty string."
        )
    if not isinstance(user_query, str) or not user_query.strip():
        return _failure_update(
            state, stage="input", message="User query must be a non-empty string."
        )

    # Valuation inputs are optional at the public request boundary. Validate
    # them only when supplied; missing values are handled after Research, at
    # the Valuation boundary, so the research task can still run independently.
    from app.valuation.models import ValuationAssumptions, ValuationInputs

    supplied_inputs = state.get("valuation_inputs")
    if supplied_inputs is not None and not isinstance(supplied_inputs, ValuationInputs):
        return _failure_update(
            state,
            stage="input",
            message="If provided, valuation_inputs must be a ValuationInputs instance.",
        )
    supplied_assumptions = state.get("valuation_assumptions")
    if supplied_assumptions is not None and not isinstance(
        supplied_assumptions, ValuationAssumptions
    ):
        return _failure_update(
            state,
            stage="input",
            message=(
                "If provided, valuation_assumptions must be a "
                "ValuationAssumptions instance."
            ),
        )

    return {
        "ticker": ticker.strip().upper(),
        "user_query": user_query.strip(),
        "current_stage": "research",
        "stage_errors": dict(state.get("stage_errors") or {}),
        "application_error": "",
    }


def run_research_stage(state: ApplicationState) -> dict[str, Any]:
    """Invoke the Research Supervisor and verify required research outputs."""
    try:
        research_query = (
            f"{state['user_query']}\n\n"
            "This is a complete investment research and decision workflow. "
            "Research all four areas: company, financial, market, and "
            "industry/macro. The downstream valuation, risk analysis, "
            "investment decision, and final report require all four outputs."
        )
        result = research_supervisor_graph.invoke(
            {"ticker": state["ticker"], "user_query": research_query}
        )
        if not isinstance(result, Mapping):
            raise StageContractError("Research output must be a mapping.")

        research_errors = result.get("research_errors") or {}
        if not isinstance(research_errors, dict):
            raise StageContractError("Research research_errors must be a mapping.")

        updates = {
            key: result.get(key)
            for key in (
                "research_plan",
                "completed_research_areas",
                "company_research",
                "financial_research",
                "market_research",
                "industry_macro_research",
                "research_errors",
                "planning_error",
                "supervisor_error",
            )
        }
        updates["research_errors"] = dict(research_errors)

        supervisor_error = result.get("supervisor_error") or result.get("planning_error")
        if supervisor_error:
            message = str(supervisor_error)
            return {
                **updates,
                **_failure_update(
                    {**state, **updates}, stage="research", message=message
                ),
            }

        missing = [field for field in _REQUIRED_RESEARCH_FIELDS if updates.get(field) is None]
        if missing:
            message = "Required research output(s) missing: " + ", ".join(missing)
            if research_errors:
                details = "; ".join(f"{key}: {value}" for key, value in research_errors.items())
                message = f"{message}. Research errors: {details}"
            return {
                **updates,
                **_failure_update(
                    {**state, **updates}, stage="research", message=message
                ),
            }
        if research_errors:
            details = "; ".join(f"{key}: {value}" for key, value in research_errors.items())
            return {
                **updates,
                **_failure_update(
                    {**state, **updates},
                    stage="research",
                    message=f"One or more research areas failed: {details}",
                ),
            }

        validate_ticker_consistency(
            state["ticker"],
            company_research=updates["company_research"],
            financial_research=updates["financial_research"],
            market_research=updates["market_research"],
            industry_macro_research=updates["industry_macro_research"],
        )
        expected_types = {
            "company_research": CompanyResearchResult,
            "financial_research": FinancialResearchResult,
            "market_research": MarketResearchResult,
            "industry_macro_research": IndustryMacroResearchResult,
        }
        for key, expected_type in expected_types.items():
            if not isinstance(updates[key], expected_type):
                raise StageContractError(
                    f"Research field '{key}' must be {expected_type.__name__}."
                )

        return {
            **updates,
            "current_stage": "valuation",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "application_error": "",
        }
    except Exception as exc:
        return _failure_update(
            state, stage="research", message=str(exc)
        )


def route_after_research(state: ApplicationState) -> str:
    return "continue" if not state.get("application_error") and not state.get("stage_errors", {}).get("research") else "end"


def run_valuation_stage(state: ApplicationState) -> dict[str, Any]:
    """Validate valuation dependencies, then run the deterministic valuation."""
    from app.valuation.models import ValuationAssumptions, ValuationInputs

    # The public request may omit these fields. Do not invent financial data or
    # silently choose assumptions; stop at this boundary with an actionable
    # error after Research has completed.
    if not isinstance(state.get("valuation_inputs"), ValuationInputs):
        return _failure_update(
            state,
            stage="valuation",
            message=(
                "Valuation cannot run: ValuationInputs are missing. Provide "
                "explicit EPS or integrate a trusted valuation-input provider."
            ),
            result_key="valuation",
            error_key="valuation_error",
        )
    if not isinstance(state.get("valuation_assumptions"), ValuationAssumptions):
        return _failure_update(
            state,
            stage="valuation",
            message=(
                "Valuation cannot run: ValuationAssumptions are missing. Provide "
                "an explicit valuation multiple and rationale; no default is applied."
            ),
            result_key="valuation",
            error_key="valuation_error",
        )

    try:
        raw = valuation_graph.invoke(
            {
                "ticker": state["ticker"],
                "company_research": state["company_research"],
                "valuation_inputs": state["valuation_inputs"],
                "valuation_assumptions": state["valuation_assumptions"],
            }
        )
        normalized = normalize_valuation_output(raw)
        result = normalized["valuation"]
        error = normalized["valuation_error"]
        if error:
            return _failure_update(
                state, stage="valuation", message=error,
                result_key="valuation", error_key="valuation_error",
            )
        if not isinstance(result, ValuationResult):
            raise StageContractError("Valuation result must be a ValuationResult.")
        validate_ticker_consistency(state["ticker"], valuation=result)
        return {
            "valuation": result,
            "valuation_error": "",
            "current_stage": "risk",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "application_error": "",
        }
    except Exception as exc:
        return _failure_update(
            state, stage="valuation", message=str(exc),
            result_key="valuation", error_key="valuation_error",
        )


def route_after_valuation(state: ApplicationState) -> str:
    return "continue" if state.get("valuation") is not None and not state.get("valuation_error") else "end"


def run_risk_stage(state: ApplicationState) -> dict[str, Any]:
    try:
        raw = risk_graph.invoke(
            {
                "ticker": state["ticker"],
                "company_research": state["company_research"],
                "financial_research": state["financial_research"],
                "market_research": state["market_research"],
                "industry_macro_research": state["industry_macro_research"],
                "valuation": state["valuation"],
            }
        )
        normalized = normalize_stage_output(
            raw, stage_name="Risk", result_key="risk_analysis", error_key="risk_error"
        )
        result, error = normalized["risk_analysis"], normalized["risk_error"]
        if error:
            return _failure_update(
                state, stage="risk", message=error,
                result_key="risk_analysis", error_key="risk_error",
            )
        if not isinstance(result, RiskAnalysis):
            raise StageContractError("Risk result must be a RiskAnalysis.")
        validate_ticker_consistency(state["ticker"], risk_analysis=result)
        return {
            "risk_analysis": result,
            "risk_error": "",
            "current_stage": "investment_decision",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "application_error": "",
        }
    except Exception as exc:
        return _failure_update(
            state, stage="risk", message=str(exc),
            result_key="risk_analysis", error_key="risk_error",
        )


def route_after_risk(state: ApplicationState) -> str:
    return "continue" if state.get("risk_analysis") is not None and not state.get("risk_error") else "end"


def run_decision_stage(state: ApplicationState) -> dict[str, Any]:
    try:
        raw = investment_decision_graph.invoke(
            {
                "ticker": state["ticker"],
                "company_research": state["company_research"],
                "financial_research": state["financial_research"],
                "market_research": state["market_research"],
                "industry_macro_research": state["industry_macro_research"],
                "valuation": state["valuation"],
                "risk_analysis": state["risk_analysis"],
            }
        )
        normalized = normalize_stage_output(
            raw,
            stage_name="Investment Decision",
            result_key="investment_decision",
            error_key="decision_error",
        )
        result, error = normalized["investment_decision"], normalized["decision_error"]
        if error:
            return _failure_update(
                state, stage="investment_decision", message=error,
                result_key="investment_decision", error_key="decision_error",
            )
        if not isinstance(result, InvestmentDecision):
            raise StageContractError("Decision result must be an InvestmentDecision.")
        validate_ticker_consistency(state["ticker"], investment_decision=result)
        return {
            "investment_decision": result,
            "decision_error": "",
            "current_stage": "report_assembly",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "application_error": "",
        }
    except Exception as exc:
        return _failure_update(
            state, stage="investment_decision", message=str(exc),
            result_key="investment_decision", error_key="decision_error",
        )


def route_after_decision(state: ApplicationState) -> str:
    return "continue" if state.get("investment_decision") is not None and not state.get("decision_error") else "end"


def assemble_report_stage(state: ApplicationState) -> dict[str, Any]:
    try:
        report = build_investment_report(
            company_research=state["company_research"],
            financial_research=state["financial_research"],
            market_research=state["market_research"],
            industry_macro_research=state["industry_macro_research"],
            valuation=state["valuation"],
            risk_analysis=state["risk_analysis"],
            investment_decision=state["investment_decision"],
        )
        return {
            "report": report,
            "report_assembly_error": "",
            "current_stage": "report_generation",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "application_error": "",
        }
    except Exception as exc:
        return _failure_update(
            state, stage="report_assembly", message=str(exc),
            result_key="report", error_key="report_assembly_error",
        )


def route_after_report_assembly(state: ApplicationState) -> str:
    return "continue" if state.get("report") is not None and not state.get("report_assembly_error") else "end"


def generate_report_stage(state: ApplicationState) -> dict[str, Any]:
    try:
        raw = report_generation_graph.invoke({"report": state["report"]})
        if not isinstance(raw, Mapping):
            raise StageContractError("Report generation output must be a mapping.")
        generated_report = raw.get("report")
        generation_error = raw.get("generation_error")
        merge_error = raw.get("merge_error")
        for key, value in (("generation_error", generation_error), ("merge_error", merge_error)):
            if value is not None and not isinstance(value, str):
                raise StageContractError(f"Report {key} must be a string or None.")
        # If narrative generation fails, the deterministic assembled report is
        # retained. The error remains explicit so callers can distinguish a
        # complete narrative report from a structured fallback report.
        if generated_report is None:
            if not generation_error and not merge_error:
                raise StageContractError(
                    "Report generation returned no report and no error."
                )
            generated_report = state["report"]
        if not isinstance(generated_report, InvestmentReport):
            raise StageContractError("Report generation result must be an InvestmentReport.")
        errors = dict(state.get("stage_errors") or {})
        if generation_error:
            errors["report_generation"] = generation_error
        if merge_error:
            errors["report_merge"] = merge_error
        application_error = ""
        if generation_error or merge_error:
            details = "; ".join(
                message for message in (generation_error, merge_error) if message
            )
            application_error = f"Report generation incomplete: {details}"
        return {
            "report": generated_report,
            "report_generation_error": generation_error or "",
            "report_merge_error": merge_error or "",
            "current_stage": "completed" if not application_error else "report_generation",
            "stage_errors": errors,
            "application_error": application_error,
        }
    except Exception as exc:
        message = str(exc) or type(exc).__name__
        errors = _stage_errors(state, "report_generation", message)
        return {
            "report": state.get("report"),
            "report_generation_error": message,
            "report_merge_error": state.get("report_merge_error", ""),
            "current_stage": "report_generation",
            "stage_errors": errors,
            "application_error": f"Report generation failed: {message}",
        }


def finalize_application(state: ApplicationState) -> dict[str, Any]:
    """Ensure the public output has predictable error containers."""
    return {
        "ticker": state.get("ticker", ""),
        "company_research": state.get("company_research"),
        "financial_research": state.get("financial_research"),
        "market_research": state.get("market_research"),
        "industry_macro_research": state.get("industry_macro_research"),
        "valuation": state.get("valuation"),
        "valuation_error": state.get("valuation_error", ""),
        "risk_analysis": state.get("risk_analysis"),
        "risk_error": state.get("risk_error", ""),
        "investment_decision": state.get("investment_decision"),
        "decision_error": state.get("decision_error", ""),
        "report": state.get("report"),
        "research_errors": dict(state.get("research_errors") or {}),
        "stage_errors": dict(state.get("stage_errors") or {}),
        "report_assembly_error": state.get("report_assembly_error", ""),
        "report_generation_error": state.get("report_generation_error", ""),
        "report_merge_error": state.get("report_merge_error", ""),
        "application_error": state.get("application_error", ""),
    }


def build_application_graph():
    """Compile the production Application workflow graph."""
    builder = StateGraph(
        ApplicationState,
        input_schema=ApplicationInputState,
        output_schema=ApplicationOutputState,
    )
    builder.add_node("validate_input", validate_application_input)
    builder.add_node("research", run_research_stage)
    builder.add_node("valuation", run_valuation_stage)
    builder.add_node("risk", run_risk_stage)
    builder.add_node("investment_decision", run_decision_stage)
    builder.add_node("report_assembly", assemble_report_stage)
    builder.add_node("report_generation", generate_report_stage)
    builder.add_node("finalize", finalize_application)

    builder.add_edge(START, "validate_input")
    builder.add_conditional_edges(
        "validate_input",
        lambda state: "continue" if not state.get("application_error") else "end",
        {"continue": "research", "end": "finalize"},
    )
    builder.add_conditional_edges(
        "research", route_after_research,
        {"continue": "valuation", "end": "finalize"},
    )
    builder.add_conditional_edges(
        "valuation", route_after_valuation,
        {"continue": "risk", "end": "finalize"},
    )
    builder.add_conditional_edges(
        "risk", route_after_risk,
        {"continue": "investment_decision", "end": "finalize"},
    )
    builder.add_conditional_edges(
        "investment_decision", route_after_decision,
        {"continue": "report_assembly", "end": "finalize"},
    )
    builder.add_conditional_edges(
        "report_assembly", route_after_report_assembly,
        {"continue": "report_generation", "end": "finalize"},
    )
    builder.add_edge("report_generation", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile()


risk_graph = build_risk_graph()
investment_decision_graph = build_investment_decision_graph()
application_graph = build_application_graph()
