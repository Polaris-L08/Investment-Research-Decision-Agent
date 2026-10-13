
"""Interactive demonstration of the investment research approval workflow."""

import json
import uuid

from langgraph.types import Command

from app.graph.runtime import (
    build_thread_config,
    create_application_graph,
)


def print_json(title: str, data) -> None:
    print(f"\n{'=' * 20} {title} {'=' * 20}")
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def main() -> None:
    print("\nInvestment Research Agent - Approval Demo")
    print("=" * 55)

    ticker = input("请输入研究股票代码，例如 AAPL: ").strip().upper()
    if not ticker:
        print("股票代码不能为空，程序结束。")
        return

    user_query = input(
        "请输入研究需求（直接回车使用默认需求）: "
    ).strip()

    if not user_query:
        user_query = (
            f"研究 {ticker} 的公司基本面、财务状况、市场表现和行业宏观环境，"
            "并在有充分依据的情况下形成投资决策和研究报告。"
        )

    # 每次演示创建独立的工作流线程，避免和其他演示混淆。
    thread_id = f"approval-demo-{uuid.uuid4().hex}"
    config = build_thread_config(thread_id)

    print(f"\n工作流线程 ID: {thread_id}")
    print("正在创建工作流并提交研究申请……")

    # 使用项目的正式 Application Graph 和 SQLite Checkpointer。
    graph = create_application_graph()

    initial_state = {
        "ticker": ticker,
        "user_query": user_query,
    }

    # 首次执行：预期工作流运行至人工审批节点后暂停。
    result = graph.invoke(initial_state, config=config)

    interrupts = result.get("__interrupt__", ())

    if not interrupts:
        print("\n工作流没有产生人工审批中断。")
        print("请检查当前代码是否已集成 Phase 10 HITL。")
        print_json("当前工作流结果", result)
        return

    print("\n工作流已暂停，等待人工审批。")
    print_json(
        "待审批信息",
        [item.value for item in interrupts],
    )

    print("\n请选择审批决定：")
    print("1. 批准（approve）")
    print("2. 拒绝（reject）")

    while True:
        choice = input("请输入 1 或 2: ").strip()
        if choice in {"1", "2"}:
            break
        print("输入无效，请输入 1 或 2。")

    decision = "approve" if choice == "1" else "reject"

    reason = input("请输入审批理由: ").strip()
    if not reason:
        reason = (
            "人工审批通过。"
            if decision == "approve"
            else "人工审批拒绝。"
        )

    approval_payload = {
        "decision": decision,
        "reason": reason,
    }

    print_json("提交的审批决定", approval_payload)
    print("\n正在恢复工作流……")

    # 使用同一个 graph 和 thread_id 恢复原工作流。
    # Command(resume=...) 提供 interrupt() 对应的恢复值。
    final_result = graph.invoke(
        Command(resume=approval_payload),
        config=config,
    )

    print_json(
        "最终业务状态",
        {
            "ticker": final_result.get("ticker"),
            "approval_status": final_result.get("approval_status"),
            "approval_reason": final_result.get("approval_reason"),
            "current_stage": final_result.get("current_stage"),
            "application_error": final_result.get("application_error"),
            "stage_errors": final_result.get("stage_errors"),
        },
    )

    report_markdown = final_result.get("report_markdown")
    if report_markdown:
        print("\n最终研究报告：")
        print("-" * 55)
        print(report_markdown)
        print("-" * 55)

    print("\n演示结束。")


if __name__ == "__main__":
    main()
