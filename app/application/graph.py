"""Production top-level Application Graph.

The graph orchestrates the business stages in this order:
Research -> Valuation -> Risk -> Investment Decision -> Report.
Report assembly, narrative generation, and Markdown rendering are encapsulated
in the Report Graph.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.agents.investment_decision import investment_decision_graph
from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.agents.report import report_graph
from app.agents.research_supervisor import research_supervisor_graph
from app.agents.risk import risk_graph
from app.agents.valuation import valuation_graph
from app.application.contracts import (
    StageContractError,
    normalize_stage_output,
    normalize_valuation_output,
    validate_ticker_consistency,
)
from app.application.errors import ErrorCategory, make_error_detail
from app.application.state import (
    ApplicationInputState,
    ApplicationOutputState,
    ApplicationState,
)
from app.investment.models import InvestmentDecision
from app.memory import MemoryService, SQLiteMemoryRepository
from app.memory.context import MemoryContextPacker
from app.memory.workflow import make_memory_context_node, make_memory_capture_node
from app.report import InvestmentReport
from app.risk.models import RiskAnalysis
from app.valuation.models import ValuationResult, ValuationAssumptions, ValuationInputs

_REQUIRED_RESEARCH_FIELDS = (
    "company_research",
    "financial_research",
    "market_research",
    "industry_macro_research",
)

_RESEARCH_FIELD_TO_AREA = {
    "company_research": "company",
    "financial_research": "financial",
    "market_research": "market",
    "industry_macro_research": "industry_macro",
}


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
    exc: Exception | None = None,
    error_code: str | None = None,
    error_category: ErrorCategory | None = None,
    retryable: bool | None = None,
    handling_owner: str | None = None,
) -> dict[str, Any]:
    """生成统一失败状态，并将结构化错误追加到本次执行的 State。

    这里不执行重试或降级；它只记录失败事实及分类结果，随后由 Graph
    的条件边决定是否允许进入下游阶段。若有原始异常，必须传入 ``exc``，
    以免把 Provider、超时、契约错误等不同故障都压扁成普通字符串。
    """
    # 子图只返回错误字符串时，不猜测底层异常类型或可重试性；只有捕获到
    # 原始异常时，才由错误分类器给出更具体的诊断。
    normalized_message = message.strip() or (
        (str(exc).strip() or type(exc).__name__)
        if exc is not None
        else "Stage failed without an error message."
    )
    detail = make_error_detail(
        stage=stage,
        message=normalized_message,
        exc=exc,
        code=error_code,
        category=error_category,
        retryable=retryable,
        handling_owner=handling_owner,
    )
    previous_details = state.get("error_details") or []
    if not isinstance(previous_details, list):
        # State 是内部契约；如果历史状态本身损坏，也要保留当前故障的可诊断性。
        previous_details = []

    update: dict[str, Any] = {
        "current_stage": stage,
        # 统一生命周期状态是路由的首要依据；错误详情用于诊断，不代替路由状态。
        "execution_status": "failed",
        "stage_errors": _stage_errors(state, stage, normalized_message),
        "error_details": [*previous_details, detail],
        "application_error": f"{stage} failed: {normalized_message}",
    }
    if result_key:
        update[result_key] = None
    if error_key:
        update[error_key] = normalized_message
    return update


def validate_application_input(state: ApplicationState) -> dict[str, Any]:
    """验证公开请求，并初始化本次执行的错误集合。

    估值输入允许在请求入口缺省，因为研究阶段可以独立执行；但若调用方
    显式传入错误类型，则应立即拒绝，不能等到后续阶段才暴露类型错误。
    """
    ticker = state.get("ticker", "")
    user_query = state.get("user_query", "")
    if not isinstance(ticker, str) or not ticker.strip():
        return _failure_update(
            state, stage="input", message="Ticker must be a non-empty string.",
            error_code="INVALID_TICKER", error_category="input_validation",
            retryable=False, handling_owner="application_input_boundary",
        )
    if not isinstance(user_query, str) or not user_query.strip():
        return _failure_update(
            state, stage="input", message="User query must be a non-empty string.",
            error_code="INVALID_USER_QUERY", error_category="input_validation",
            retryable=False, handling_owner="application_input_boundary",
        )

    # Valuation inputs are optional at the public request boundary. Validate
    # them only when supplied; missing values are handled after Research, at
    # the Valuation boundary, so the research task can still run independently.
    supplied_inputs = state.get("valuation_inputs")
    if supplied_inputs is not None and not isinstance(supplied_inputs, ValuationInputs):
        return _failure_update(
            state,
            stage="input",
            message="If provided, valuation_inputs must be a ValuationInputs instance.",
            error_code="INVALID_VALUATION_INPUTS_TYPE",
            error_category="input_validation",
            retryable=False,
            handling_owner="application_input_boundary",
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
            error_code="INVALID_VALUATION_ASSUMPTIONS_TYPE",
            error_category="input_validation",
            retryable=False,
            handling_owner="application_input_boundary",
        )

    return {
        "ticker": ticker.strip().upper(),
        "user_query": user_query.strip(),
        "current_stage": "approval",
        "execution_status": "running",
        "approval_status": "pending",
        "approval_reason": "",
        "stage_errors": dict(state.get("stage_errors") or {}),
        "error_details": list(state.get("error_details") or []),
        "application_error": "",
    }



def approval_gate(state: ApplicationState) -> dict[str, Any]:
    """暂停工作流等待人工审批，并校验恢复执行时传入的审批结果。

    ``interrupt`` 的恢复值属于外部输入，不能因为它来自 HITL 流程就被视为可信。
    非法恢复值记录为不可重试的输入契约错误；用户明确拒绝则是业务终态，不能
    误记为执行失败。
    """

    decision = interrupt(
        {
            "type": "research_approval",
            "ticker": state["ticker"],
            "research_task": state["user_query"],
            "reason_for_approval": (
                "Human approval is required before investment research starts."
            ),
            "requested_action": "run_research",
            "approval_required": True,
        }
    )

    # A resume value is untrusted input and must be validated.
    if not isinstance(decision, dict):
        message = "Approval response must be a dictionary."
        return {
            **_failure_update(
                state, stage="approval", message=message,
                error_code="INVALID_APPROVAL_RESPONSE_TYPE",
                error_category="input_validation", retryable=False,
                handling_owner="approval_boundary",
            ),
            "approval_status": "invalid",
            "approval_reason": message,
        }

    action = decision.get("decision")
    reason = decision.get("reason", "")

    if not isinstance(action, str) or action not in {"approve", "reject"}:
        message = "Decision must be 'approve' or 'reject'."
        return {
            **_failure_update(
                state, stage="approval", message=message,
                error_code="INVALID_APPROVAL_DECISION",
                error_category="input_validation", retryable=False,
                handling_owner="approval_boundary",
            ),
            "approval_status": "invalid",
            "approval_reason": message,
        }

    if not isinstance(reason, str):
        message = "Approval reason must be a string."
        return {
            **_failure_update(
                state, stage="approval", message=message,
                error_code="INVALID_APPROVAL_REASON",
                error_category="input_validation", retryable=False,
                handling_owner="approval_boundary",
            ),
            "approval_status": "invalid",
            "approval_reason": message,
        }

    if action == "reject":
        return {
            "approval_status": "rejected",
            "approval_reason": reason.strip(),
            "current_stage": "rejected",
            "execution_status": "rejected",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "error_details": list(state.get("error_details") or []),
            "application_error": "",
        }

    return {
        "approval_status": "approved",
        "approval_reason": reason.strip(),
        "current_stage": "research",
        "execution_status": "running",
        "stage_errors": dict(state.get("stage_errors") or {}),
        "error_details": list(state.get("error_details") or []),
        "application_error": "",
    }


def route_after_approval(state: ApplicationState) -> str:
    """仅允许无错误的有效审批进入 Research。"""
    if (
        state.get("approval_status") == "approved"
        and state.get("execution_status") == "running"
        and not state.get("application_error")
        and not (state.get("stage_errors") or {})
        and not (state.get("error_details") or [])
    ):
        return "continue"
    return "end"



def run_research_stage(state: ApplicationState) -> dict[str, Any]:
    """Invoke the Research Supervisor and verify required research outputs."""
    try:
        memory_context = state.get("memory_context", "")
        memory_section = (
            "Long-term memory context (untrusted background only; not evidence):\n"
            + memory_context
            if memory_context else ""
        )
        research_query = (
            f"{state['user_query']}\n\n"
            f"{memory_section}\n\n"
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
                "valuation_inputs",
                "valuation_assumptions",
                "valuation_research_error",
            )
        }
        # Application-level overrides are explicit and take precedence.
        if state.get("valuation_inputs") is not None:
            updates["valuation_inputs"] = state["valuation_inputs"]
        if state.get("valuation_assumptions") is not None:
            updates["valuation_assumptions"] = state["valuation_assumptions"]

        updates["research_errors"] = dict(research_errors)

        supervisor_error = result.get("supervisor_error") or result.get("planning_error")
        if supervisor_error:
            message = str(supervisor_error)
            return {
                **updates,
                **_failure_update(
                    {**state, **updates}, stage="research", message=message,
                    error_code="RESEARCH_SUPERVISOR_REPORTED_FAILURE",
                ),
            }

        expected_types = {
            "company_research": CompanyResearchResult,
            "financial_research": FinancialResearchResult,
            "market_research": MarketResearchResult,
            "industry_macro_research": IndustryMacroResearchResult,
        }

        # Validate every result that is present before classifying the run as
        # partial. A malformed object must not be treated as usable evidence.
        available_research: dict[str, Any] = {}
        for key, expected_type in expected_types.items():
            research_result = updates.get(key)
            if research_result is None:
                continue
            if not isinstance(research_result, expected_type):
                raise StageContractError(
                    f"Research field '{key}' must be {expected_type.__name__}."
                )
            available_research[key] = research_result

        if available_research:
            validate_ticker_consistency(
                state["ticker"],
                **available_research,
            )

        degraded_areas: list[str] = []
        degradation_reasons: dict[str, str] = {}
        for field, area in _RESEARCH_FIELD_TO_AREA.items():
            research_result = updates.get(field)
            if research_result is None:
                continue
            status = getattr(research_result, "data_status", None)
            reason = getattr(research_result, "degradation_reason", None)
            if status not in {"complete", "degraded"}:
                raise StageContractError(
                    f"Research result '{area}' has an invalid data_status."
                )
            if status == "degraded":
                if not isinstance(reason, str) or not reason.strip():
                    raise StageContractError(
                        f"Degraded research result '{area}' must include degradation_reason."
                    )
                degraded_areas.append(area)
                degradation_reasons[area] = reason.strip()
            elif reason != "":
                raise StageContractError(
                    f"Complete research result '{area}' must have an empty degradation_reason."
                )

        updates["degraded_research_areas"] = degraded_areas
        updates["research_degradation_reasons"] = degradation_reasons

        missing = [
            field
            for field in _REQUIRED_RESEARCH_FIELDS
            if updates.get(field) is None
        ]
        if missing or research_errors:
            # Partial means at least one validated research result is usable,
            # but the required evidence set is incomplete. It is deliberately
            # not a successful Application run: downstream valuation, risk,
            # decision, and report stages must not execute with missing inputs.
            updates["research_data_status"] = (
                "partial" if available_research else "not_available"
            )
            failed_areas = set(research_errors)
            failed_areas.update(
                _RESEARCH_FIELD_TO_AREA[field]
                for field in missing
                if field in _RESEARCH_FIELD_TO_AREA
            )
            area_order = list(_RESEARCH_FIELD_TO_AREA.values())
            updates["failed_research_areas"] = [
                area for area in area_order if area in failed_areas
            ] + sorted(failed_areas.difference(area_order))

            details: list[str] = []
            if missing:
                details.append(
                    "Required research output(s) missing: " + ", ".join(missing)
                )
            if research_errors:
                error_details = "; ".join(
                    f"{key}: {value}" for key, value in research_errors.items()
                )
                details.append("Research errors: " + error_details)
            message = ". ".join(details)
            return {
                **updates,
                **_failure_update(
                    {**state, **updates},
                    stage="research",
                    message=message,
                    error_code="RESEARCH_EVIDENCE_INCOMPLETE",
                ),
            }

        updates["failed_research_areas"] = []
        updates["research_data_status"] = (
            "degraded" if degraded_areas else "complete"
        )
        if updates.get("valuation_inputs") is not None and not isinstance(
            updates["valuation_inputs"], ValuationInputs
        ):
            raise StageContractError("Research field 'valuation_inputs' must be ValuationInputs or None.")
        if updates.get("valuation_assumptions") is not None and not isinstance(
            updates["valuation_assumptions"], ValuationAssumptions
        ):
            raise StageContractError("Research field 'valuation_assumptions' must be ValuationAssumptions or None.")


        return {
            **updates,
            "current_stage": "valuation",
            "execution_status": "running",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "application_error": "",
        }
    except Exception as exc:
        return _failure_update(
            state, stage="research", message=str(exc), exc=exc
        )


def route_after_research(state: ApplicationState) -> str:
    """仅当研究证据完整且错误契约一致时，才允许进入估值阶段。

    execution_status 是主要生命周期标记；业务错误、阶段错误和结构化错误
    都是防御性检查，防止 State 合并后出现“有结果但实际失败”的错误路由。
    """
    required_outputs_present = all(
        state.get(field) is not None for field in _REQUIRED_RESEARCH_FIELDS
    )
    can_continue = (
        state.get("execution_status") == "running"
        and required_outputs_present
        and state.get("research_data_status") in {"complete", "degraded"}
        and not state.get("application_error")
        and not (state.get("stage_errors") or {})
        and not (state.get("error_details") or [])
    )
    return "continue" if can_continue else "end"


def run_valuation_stage(state: ApplicationState) -> dict[str, Any]:
    """Validate valuation dependencies, then run the deterministic valuation."""

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
            error_code="VALUATION_INPUTS_MISSING",
            error_category="business_input",
            retryable=False,
            handling_owner="valuation_input_boundary",
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
            error_code="VALUATION_ASSUMPTIONS_MISSING",
            error_category="business_input",
            retryable=False,
            handling_owner="valuation_input_boundary",
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
            "execution_status": "running",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "application_error": "",
        }
    except Exception as exc:
        return _failure_update(
            state, stage="valuation", message=str(exc),
            result_key="valuation", error_key="valuation_error", exc=exc,
        )


def route_after_valuation(state: ApplicationState) -> str:
    """只有估值结果有效且没有任何遗留错误时，才允许运行 Risk。"""
    can_continue = (
        state.get("execution_status") == "running"
        and state.get("valuation") is not None
        and not state.get("valuation_error")
        and not (state.get("stage_errors") or {})
        and not (state.get("error_details") or [])
        and not state.get("application_error")
    )
    return "continue" if can_continue else "end"


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
            "execution_status": "running",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "application_error": "",
        }
    except Exception as exc:
        return _failure_update(
            state, stage="risk", message=str(exc),
            result_key="risk_analysis", error_key="risk_error", exc=exc,
        )


def route_after_risk(state: ApplicationState) -> str:
    """阻止 Investment Decision 消费缺失、失败或状态不一致的风险结果。"""
    can_continue = (
        state.get("execution_status") == "running"
        and state.get("risk_analysis") is not None
        and not state.get("risk_error")
        and not (state.get("stage_errors") or {})
        and not (state.get("error_details") or [])
        and not state.get("application_error")
    )
    return "continue" if can_continue else "end"


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
            "current_stage": "report",
            "execution_status": "running",
            "stage_errors": dict(state.get("stage_errors") or {}),
            "application_error": "",
        }
    except Exception as exc:
        return _failure_update(
            state, stage="investment_decision", message=str(exc),
            result_key="investment_decision", error_key="decision_error", exc=exc,
        )


def route_after_decision(state: ApplicationState) -> str:
    """只有投资决策结果有效且工作流没有遗留错误时，才允许进入报告阶段。"""
    can_continue = (
        state.get("execution_status") == "running"
        and state.get("investment_decision") is not None
        and not state.get("decision_error")
        and not (state.get("stage_errors") or {})
        and not (state.get("error_details") or [])
        and not state.get("application_error")
    )
    return "continue" if can_continue else "end"


def run_report_stage(state: ApplicationState) -> dict[str, Any]:
    """执行报告子图，并把内部报告错误统一映射到 Application 契约。

    报告子图可以返回部分诊断信息，但只有在结构化报告和 Markdown 都存在、
    且所有报告子阶段均未报告错误时，顶层工作流才可以标记为 completed。
    否则会把故障写入统一错误集合，并由 Memory 节点跳过长期历史写入。
    """
    try:
        raw = report_graph.invoke(
            {
                "company_research": state["company_research"],
                "financial_research": state["financial_research"],
                "market_research": state["market_research"],
                "industry_macro_research": state["industry_macro_research"],
                "valuation": state["valuation"],
                "risk_analysis": state["risk_analysis"],
                "investment_decision": state["investment_decision"],
            }
        )
        if not isinstance(raw, Mapping):
            raise StageContractError("Report Graph output must be a mapping.")

        report = raw.get("report")
        if report is not None and not isinstance(report, InvestmentReport):
            raise StageContractError("Report Graph 'report' must be an InvestmentReport or None.")
        if report is not None:
            # 报告是最终对外结果，必须确认其证券代码与本次请求一致。
            validate_ticker_consistency(state["ticker"], report=report)

        error_fields = (
            ("report_assembly_error", "report_assembly"),
            ("report_generation_error", "report_generation"),
            ("report_merge_error", "report_merge"),
            ("report_rendering_error", "report_rendering"),
        )
        stage_errors = dict(state.get("stage_errors") or {})
        # 结构化错误不能只存在于 stage_errors 字符串字典中；逐个子阶段记录
        # 错误详情，才能保留错误来源和“根异常未知”的语义。
        error_details = list(state.get("error_details") or [])
        report_errors: list[str] = []
        normalized_errors: dict[str, str] = {}
        for field_name, stage_name in error_fields:
            value = raw.get(field_name, "")
            if value is None:
                value = ""
            if not isinstance(value, str):
                raise StageContractError(f"Report Graph field '{field_name}' must be a string or None.")
            normalized_errors[field_name] = value.strip()
            if normalized_errors[field_name]:
                stage_errors[stage_name] = normalized_errors[field_name]
                report_errors.append(f"{stage_name}: {normalized_errors[field_name]}")
                error_details.append(
                    make_error_detail(
                        stage=stage_name,
                        message=normalized_errors[field_name],
                        code="REPORT_SUBSTAGE_REPORTED_FAILURE",
                        handling_owner="report_graph_boundary",
                    )
                )

        report_markdown = raw.get("report_markdown", "")
        if report_markdown is None:
            report_markdown = ""
        if not isinstance(report_markdown, str):
            raise StageContractError("Report Graph field 'report_markdown' must be a string.")
        report_markdown = report_markdown.strip()

        # 没有子阶段错误却缺少报告主体，说明子图违反了成功输出契约。
        # 不能仅凭 error 字段为空就把空报告标记为成功。
        if not report_errors and (report is None or not report_markdown):
            raise StageContractError(
                "Report Graph reported no errors but did not return both a structured report and non-empty Markdown."
            )

        degraded_areas = list(state.get("degraded_research_areas") or [])
        if degraded_areas:
            reasons = state.get("research_degradation_reasons") or {}
            caveat_lines = [
                "## Research data limitations",
                "This report contains degraded research input and must not be treated as a fully complete research result.",
            ]
            for area in degraded_areas:
                reason = reasons.get(area, "Degraded result; reason was not supplied.")
                caveat_lines.append(f"- {area}: {reason}")
            caveat = "\n".join(caveat_lines)
            report_markdown = f"{caveat}\n\n---\n\n{report_markdown}" if report_markdown else caveat

        # 即使当前报告子图没有返回错误，之前阶段遗留的错误也不能被本节点清空。
        prior_errors_exist = bool(
            state.get("application_error")
            or state.get("stage_errors")
            or state.get("error_details")
        )
        application_error = ""
        if report_errors:
            application_error = "Report stage ended with errors: " + "; ".join(report_errors)
        elif prior_errors_exist:
            application_error = state.get("application_error") or (
                "Report stage cannot complete because prior workflow errors remain."
            )

        workflow_failed = bool(report_errors or prior_errors_exist)

        return {
            "report": report,
            **normalized_errors,
            "report_markdown": report_markdown,
            "current_stage": "report" if workflow_failed else "completed",
            "execution_status": "failed" if workflow_failed else "completed",
            "stage_errors": stage_errors,
            "error_details": error_details,
            "application_error": application_error,
        }
    except Exception as exc:
        message = str(exc) or type(exc).__name__
        return {
            **_failure_update(
                state, stage="report", message=message, exc=exc
            ),
            # 报告子图调用或契约校验失败时，不保留可能来自旧状态的报告对象。
            "report": None,
            "report_assembly_error": state.get("report_assembly_error", ""),
            "report_generation_error": state.get("report_generation_error", ""),
            "report_merge_error": state.get("report_merge_error", ""),
            "report_rendering_error": state.get("report_rendering_error", ""),
            "report_markdown": state.get("report_markdown", ""),
        }


def _terminal_execution_status(state: Mapping[str, Any]) -> str:
    """在公开输出边界规范化终态，避免把不一致的 State 报告为成功。

    用户拒绝审批属于业务终态；除此之外，任何错误字段都优先于可能陈旧的
    execution_status。终结节点不得向调用方返回 running 这种非终态状态。
    """
    if state.get("approval_status") == "rejected":
        return "rejected"
    if (
        state.get("application_error")
        or state.get("stage_errors")
        or state.get("error_details")
    ):
        return "failed"

    status = state.get("execution_status")
    if status in {"completed", "failed", "rejected"}:
        return status
    if state.get("current_stage") == "completed":
        return "completed"
    # A terminal route without an explicit terminal lifecycle is a contract
    # violation. Fail closed rather than exposing an ambiguous "running" run.
    return "failed"


def finalize_application(state: ApplicationState) -> dict[str, Any]:
    """Return the stable public output contract for the application run."""
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
        "report_markdown": state.get("report_markdown", ""),
        "report_rendering_error": state.get("report_rendering_error", ""),
        "research_errors": dict(state.get("research_errors") or {}),
        "research_data_status": state.get("research_data_status", "not_available"),
        "failed_research_areas": list(state.get("failed_research_areas") or []),
        "degraded_research_areas": list(state.get("degraded_research_areas") or []),
        "research_degradation_reasons": dict(state.get("research_degradation_reasons") or {}),
        "stage_errors": dict(state.get("stage_errors") or {}),
        # 将可序列化的结构化错误作为稳定公开诊断契约输出。
        "error_details": list(state.get("error_details") or []),
        "execution_status": _terminal_execution_status(state),
        "report_assembly_error": state.get("report_assembly_error", ""),
        "report_generation_error": state.get("report_generation_error", ""),
        "report_merge_error": state.get("report_merge_error", ""),
        "application_error": state.get("application_error", ""),
        "approval_status": state.get("approval_status", ""),
        "approval_reason": state.get("approval_reason", ""),
        "memory_context_error": state.get("memory_context_error", ""),
        "memory_capture_decision": state.get("memory_capture_decision", ""),
        "memory_capture_reason": state.get("memory_capture_reason", ""),
        "memory_capture_memory_id": state.get("memory_capture_memory_id", ""),
        "memory_capture_error": state.get("memory_capture_error", ""),
    }


def _build_default_memory_service() -> MemoryService:
    """Create persistent cross-run memory; override its path with an environment variable."""
    database_path = os.environ.get("MEMORY_DATABASE_PATH", "data/memory.sqlite3")
    return MemoryService(SQLiteMemoryRepository(database_path))


def build_application_graph(
        *,
        checkpointer: Any = None,
        memory_service: MemoryService | None = None,
        memory_context_packer: MemoryContextPacker | None = None,
        memory_history_ttl_days: int = 180,
        enable_default_memory: bool = True,
):
    """Compile the production Application workflow graph.

    Pass ``memory_service`` to inject a configured service in tests/deployments.
    When it is omitted (or None) and ``enable_default_memory`` is true, the graph
    creates a persistent SQLite-backed service. Set ``enable_default_memory``
    false to intentionally disable memory for a test or isolated deployment.
    """
    if memory_history_ttl_days < 1:
        raise ValueError("memory_history_ttl_days must be >= 1")
    if memory_service is None and enable_default_memory:
        memory_service = _build_default_memory_service()

    builder = StateGraph(ApplicationState, input_schema=ApplicationInputState, output_schema=ApplicationOutputState)
    builder.add_node("validate_input", validate_application_input)
    builder.add_node("approval_gate", approval_gate)
    builder.add_node(
        "load_memory_context",
        make_memory_context_node(memory_service, context_packer=memory_context_packer),
    )
    builder.add_node("research", run_research_stage)

    builder.add_node("valuation", run_valuation_stage)
    builder.add_node("risk", run_risk_stage)
    builder.add_node("investment_decision", run_decision_stage)

    builder.add_node("report", run_report_stage)
    builder.add_node("capture_memory", make_memory_capture_node(memory_service, history_ttl_days=memory_history_ttl_days))
    builder.add_node("finalize", finalize_application)

    builder.add_edge(START, "validate_input")
    builder.add_conditional_edges(
        "validate_input",
        lambda state: "continue" if not state.get("application_error") else "end",
        {"continue": "approval_gate", "end": "finalize"},
    )
    builder.add_conditional_edges(
        "approval_gate",
        route_after_approval,
        {"continue": "load_memory_context", "end": "finalize"},
    )
    builder.add_edge("load_memory_context", "research")
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
        {"continue": "report", "end": "finalize"},
    )
    # Capture node decides whether the report was successful; failed reports
    # still pass through it so the caller receives a clear "skipped" reason.
    builder.add_edge("report", "capture_memory")
    builder.add_edge("capture_memory", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile(checkpointer=checkpointer)


application_graph = build_application_graph()
