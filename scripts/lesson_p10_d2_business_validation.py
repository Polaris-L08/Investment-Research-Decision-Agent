from typing import Literal, TypedDict

from pydantic import BaseModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str
    confidence: int


class ApprovalState(TypedDict):
    request_id: str
    risk_level: str
    approval_status: str
    application_error: str
    downstream_executed: bool


def build_graph():
    def approval_node(state: ApprovalState):
        response = interrupt(
            {
                "request_id": state["request_id"],
                "risk_level": state["risk_level"],
                "question": "是否批准继续研究？",
            },
            response_schema=ApprovalDecision,
        )

        # 第一层：Schema 已验证结构与字段类型
        decision = response.decision

        # 第二层：业务规则验证
        if decision == "approve" and state["risk_level"] == "high":
            return {
                "approval_status": "escalation_required",
                "application_error": "",
            }

        if decision == "reject":
            return {
                "approval_status": "rejected",
                "application_error": "",
            }

        return {
            "approval_status": "approved",
            "application_error": "",
        }

    def route_after_approval(state: ApprovalState):
        if state["approval_status"] == "approved":
            return "downstream"
        return END

    def downstream_node(state: ApprovalState):
        return {"downstream_executed": True}

    builder = StateGraph(ApprovalState)
    builder.add_node("approval", approval_node)
    builder.add_node("downstream", downstream_node)

    builder.add_edge(START, "approval")
    builder.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "downstream": "downstream",
            END: END,
        },
    )
    builder.add_edge("downstream", END)

    return builder.compile(checkpointer=InMemorySaver())


def run_case(risk_level, decision, expected_status, expected_downstream):
    graph = build_graph()
    config = {
        "configurable": {
            "thread_id": f"{risk_level}-{decision}",
        }
    }

    initial_state = {
        "request_id": "REQ-001",
        "risk_level": risk_level,
        "approval_status": "pending",
        "application_error": "",
        "downstream_executed": False,
    }

    graph.invoke(initial_state, config=config)

    result = graph.invoke(
        Command(
            resume={
                "decision": decision,
                "reason": "Test",
                "confidence": 3,
            }
        ),
        config=config,
    )

    print(
        f"risk={risk_level}, decision={decision}, "
        f"status={result['approval_status']}, "
        f"downstream={result['downstream_executed']}"
    )

    assert result["approval_status"] == expected_status
    assert result["downstream_executed"] == expected_downstream


def main():
    run_case("low", "approve", "approved", True)
    run_case("high", "approve", "escalation_required", False)
    run_case("low", "reject", "rejected", False)

    print("PASS: Business validation experiments completed.")


if __name__ == "__main__":
    main()