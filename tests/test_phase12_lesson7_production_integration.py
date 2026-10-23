"""Lesson 7：生产 Application Graph 的错误恢复集成测试。

这些测试故意从 ``app.application.graph`` 构建完整生产图，只替换各阶段的
依赖函数。测试同时验证路由、调用次数和公开终态；仅测试单个节点不足以
证明生产 Graph 的错误恢复行为正确。
"""

from __future__ import annotations

from collections import Counter

import pytest

import app.application.graph as application_graph_module
from app.application.graph import build_application_graph


def _approved(_state):
    """模拟人工审批通过，绕过真实 ``interrupt``，让测试直接进入 Research。"""
    return {
        "approval_status": "approved",
        "approval_reason": "lesson 7 test approval",
        "current_stage": "research",
        "execution_status": "running",
        "stage_errors": {},
        "application_error": "",
    }


def _healthy_stage(counter: Counter[str], name: str, payload: dict):
    """创建一个“成功阶段”替身，并记录该阶段实际执行了几次。

    返回值模仿生产节点的 State 增量。Graph 会把这个增量合并到共享 State，
    随后由条件边依据 execution_status、结果字段和错误字段决定下一步。
    """
    def run(_state):
        # 每个阶段只增加一次计数，用来检测是否出现意外重复执行。
        counter[name] += 1
        return {
            **payload,
            "current_stage": name,
            "execution_status": "running",
            "stage_errors": {},
            "application_error": "",
        }

    return run


def _healthy_report(counter: Counter[str]):
    """创建成功的 Report 阶段替身。

    Report 成功时把 current_stage 设为 completed；这允许后面的
    capture_memory 和 finalize 节点走成功终态。
    """
    def run(_state):
        counter["report"] += 1
        return {
            "report": object(),
            "report_markdown": "# Test report",
            "report_assembly_error": "",
            "report_generation_error": "",
            "report_merge_error": "",
            "report_rendering_error": "",
            "current_stage": "completed",
            "execution_status": "completed",
            "stage_errors": {},
            "application_error": "",
        }

    return run


def _install_healthy_stages(monkeypatch, counter: Counter[str]):
    """把生产 Graph 的审批和五个业务阶段全部替换为确定性替身。

    这里使用 ``monkeypatch`` 是为了只影响当前测试；测试结束后 pytest 会
    自动恢复 application_graph_module 中的原始函数。
    """
    monkeypatch.setattr(application_graph_module, "approval_gate", _approved)
    monkeypatch.setattr(
        application_graph_module,
        "run_research_stage",
        _healthy_stage(
            counter,
            "research",
            {
                "company_research": object(),
                "financial_research": object(),
                "market_research": object(),
                "industry_macro_research": object(),
                "research_data_status": "complete",
            },
        ),
    )
    monkeypatch.setattr(
        application_graph_module,
        "run_valuation_stage",
        _healthy_stage(counter, "valuation", {"valuation": object(), "valuation_error": ""}),
    )
    monkeypatch.setattr(
        application_graph_module,
        "run_risk_stage",
        _healthy_stage(counter, "risk", {"risk_analysis": object(), "risk_error": ""}),
    )
    monkeypatch.setattr(
        application_graph_module,
        "run_decision_stage",
        _healthy_stage(
            counter,
            "investment_decision",
            {"investment_decision": object(), "decision_error": ""},
        ),
    )
    monkeypatch.setattr(application_graph_module, "run_report_stage", _healthy_report(counter))


def test_production_graph_normal_path_records_each_stage_once(monkeypatch):
    """正常路径：所有阶段各执行一次，并以 completed 结束。

    这是集成测试的基线。它证明测试替身满足生产 Graph 的输入/输出契约，
    同时确认没有隐式重试或重复执行。
    """
    counter: Counter[str] = Counter()
    _install_healthy_stages(monkeypatch, counter)

    graph = build_application_graph(enable_default_memory=False)
    result = graph.invoke({"ticker": "AAPL", "user_query": "Run normal integration path"})

    assert result["execution_status"] == "completed"
    assert result["application_error"] == ""
    assert result["stage_errors"] == {}
    assert result["report"] is not None
    assert counter == Counter(
        research=1, valuation=1, risk=1, investment_decision=1, report=1
    )


@pytest.mark.parametrize(
    ("stage_name", "function_name", "result_key", "error_key", "downstream"),
    [
        ("valuation", "run_valuation_stage", "valuation", "valuation_error", "risk"),
        ("risk", "run_risk_stage", "risk_analysis", "risk_error", "investment_decision"),
        (
            "investment_decision",
            "run_decision_stage",
            "investment_decision",
            "decision_error",
            "report",
        ),
    ],
)
def test_critical_stage_failure_stops_only_dependent_downstream(
    monkeypatch, stage_name, function_name, result_key, error_key, downstream
):
    """关键阶段失败后，依赖该阶段的下游节点不得执行。

    ``parametrize`` 将同一套断言复用于 Valuation、Risk 和 Decision 三种
    故障，分别验证：

    - Valuation 失败不会进入 Risk；
    - Risk 失败不会进入 Investment Decision；
    - Decision 失败不会进入 Report。

    ``fail`` 返回的是生产节点风格的失败 State 增量，而不是抛出异常，
    因为 Application Graph 的预期行为是把阶段故障转换为稳定失败输出。
    """
    counter: Counter[str] = Counter()
    _install_healthy_stages(monkeypatch, counter)

    def fail(_state):
        # 记录调用次数，并清空失败阶段的结果，避免旧结果伪装成成功。
        counter[stage_name] += 1
        message = f"Injected {stage_name} failure"
        return {
            "current_stage": stage_name,
            "execution_status": "failed",
            "stage_errors": {stage_name: message},
            "application_error": f"{stage_name} failed: {message}",
            result_key: None,
            error_key: message,
        }

    monkeypatch.setattr(application_graph_module, function_name, fail)
    result = build_application_graph(enable_default_memory=False).invoke(
        {"ticker": "AAPL", "user_query": "Inject a critical stage failure"}
    )

    assert result["execution_status"] == "failed"
    assert result["stage_errors"][stage_name]
    assert result["application_error"]
    assert counter[stage_name] == 1
    assert counter[downstream] == 0


def test_report_failure_preserves_failure_and_skips_memory_capture(monkeypatch):
    """Report 失败时保留已有报告内容，但不能写入成功研究历史。

    生产图会让 report 之后经过 capture_memory；capture 节点必须识别
    execution_status=failed，并返回 skipped，而不是把失败运行记录成成功。
    """
    counter: Counter[str] = Counter()
    _install_healthy_stages(monkeypatch, counter)

    def fail_report(_state):
        counter["report"] += 1
        return {
            "report": object(),
            "report_markdown": "# Partial report",
            "report_generation_error": "LLM unavailable",
            "report_assembly_error": "",
            "report_merge_error": "",
            "report_rendering_error": "",
            "current_stage": "report",
            "execution_status": "failed",
            "stage_errors": {"report_generation": "LLM unavailable"},
            "application_error": "Report stage ended with errors: report_generation: LLM unavailable",
        }

    monkeypatch.setattr(application_graph_module, "run_report_stage", fail_report)
    result = build_application_graph(enable_default_memory=False).invoke(
        {"ticker": "AAPL", "user_query": "Inject report failure"}
    )

    assert result["execution_status"] == "failed"
    assert result["report"] is not None
    assert result["report_markdown"] == "# Partial report"
    assert result["memory_capture_decision"] == "skipped"
    assert "successfully" not in result["memory_capture_reason"]


def test_invalid_input_is_terminal_without_running_any_stage(monkeypatch):
    """输入校验失败应在业务流程开始前终止，不执行审批或任何阶段。"""
    counter: Counter[str] = Counter()
    _install_healthy_stages(monkeypatch, counter)

    result = build_application_graph(enable_default_memory=False).invoke(
        {"ticker": "", "user_query": "invalid request"}
    )

    assert result["execution_status"] == "failed"
    assert result["stage_errors"]["input"]
    assert not counter

