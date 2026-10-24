"""Run the real production Application Graph as a Lesson 8 smoke test.

This script is intentionally different from unit tests: it does not replace
the application stages with mocks.  It builds the same top-level graph used by
the application, pauses at the real HITL approval gate, resumes the same
checkpointed thread, and prints the terminal state.

The configured provider and LLM are selected by the normal project
environment variables.  Use ``--provider-mode`` only as a convenience before
the application modules are imported; it does not create fake data or bypass
the provider factory.

Examples:
    python scripts/smoke_test_application.py --provider-mode mock
    python scripts/smoke_test_application.py --provider-mode real --ticker AAPL \
        --eps 6.0 --multiple 20 --rationale "manual smoke-test assumption"
    python scripts/smoke_test_application.py --approval reject
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _json_default(value: Any) -> Any:
    """Convert Pydantic models and enums into readable JSON for the console."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "value"):
        return value.value
    return str(value)


def _print_json(title: str, value: Any) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(value, ensure_ascii=False, indent=2, default=_json_default))


def _checkpoint_summary(graph: Any, config: dict[str, Any]) -> dict[str, Any]:
    """Read the latest checkpoint without dumping the full research state."""
    snapshot = graph.get_state(config)
    values = snapshot.values or {}
    return {
        "next": list(snapshot.next),
        "current_stage": values.get("current_stage"),
        "approval_status": values.get("approval_status"),
        "execution_status": values.get("execution_status"),
        "checkpoint_id": snapshot.config.get("configurable", {}).get("checkpoint_id"),
        "interrupt_count": len(getattr(snapshot, "tasks", ()) or ()),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", default="AAPL", help="Ticker/code to research (default: AAPL).")
    parser.add_argument(
        "--query",
        default=None,
        help="Research request; defaults to a complete investment workflow request.",
    )
    parser.add_argument(
        "--provider-mode",
        choices=("mock", "real"),
        default=None,
        help="Override PROVIDER_MODE before importing the application (optional).",
    )
    parser.add_argument(
        "--approval",
        choices=("approve", "reject"),
        default="approve",
        help="Decision submitted to the real approval interrupt (default: approve).",
    )
    parser.add_argument("--reason", default=None, help="Human approval reason.")
    parser.add_argument(
        "--eps",
        type=float,
        default=None,
        help="Explicit EPS for valuation. Omit to use the configured valuation provider.",
    )
    parser.add_argument(
        "--multiple",
        type=float,
        default=None,
        help="Explicit valuation multiple; must be supplied together with --eps.",
    )
    parser.add_argument(
        "--rationale",
        default="Explicit assumption supplied for the Lesson 8 smoke test.",
        help="Rationale for --multiple.",
    )
    parser.add_argument(
        "--checkpoint-db",
        default="data/smoke_application_checkpoints.sqlite",
        help="SQLite checkpoint database path.",
    )
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Thread ID; defaults to a unique smoke-test ID.",
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Enable the default SQLite long-term memory service for this run.",
    )
    parser.add_argument(
        "--allow-failed",
        action="store_true",
        help="Return exit code 0 for a terminal failed run, useful for diagnosing partial real-provider coverage.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    load_dotenv()
    if args.provider_mode:
        os.environ["PROVIDER_MODE"] = args.provider_mode

    if (args.eps is None) != (args.multiple is None):
        parser.error("--eps and --multiple must be supplied together.")
    if args.eps is not None and args.eps <= 0:
        parser.error("--eps must be greater than zero.")
    if args.multiple is not None and args.multiple <= 0:
        parser.error("--multiple must be greater than zero.")

    # Imports happen after environment setup so provider and LLM modules read
    # the same configuration as a normal application process.
    from langgraph.types import Command

    from app.graph.checkpointer import create_checkpointer
    from app.application.graph import build_application_graph
    from app.providers.config import ProviderSettings
    from app.providers.runtime import get_provider_bundle
    from app.valuation.models import ValuationAssumptions, ValuationInputs

    ticker = args.ticker.strip().upper()
    if not ticker:
        parser.error("--ticker must not be empty.")
    query = args.query or (
        f"Analyze {ticker}'s company, financial, market, and industry/macro condition "
        "and produce an evidence-grounded investment decision and report."
    )
    thread_id = args.thread_id or f"lesson8-smoke-{uuid.uuid4().hex}"
    config: dict[str, Any] = {
        "configurable": {
            "thread_id": thread_id,
            "memory_owner_id": os.getenv("SMOKE_MEMORY_OWNER_ID", "lesson8-user"),
            "memory_namespace": os.getenv("SMOKE_MEMORY_NAMESPACE", "investment-research"),
            "memory_source_reference": f"smoke-test:{thread_id}",
        }
    }

    settings = ProviderSettings.from_env()
    bundle = get_provider_bundle()
    print("Investment Application Graph smoke test")
    print(f"Provider mode: {settings.mode} (bundle={bundle.mode})")
    print(f"Provider source: {settings.real_provider_source}")
    print(f"Ticker: {ticker}")
    print(f"Thread ID: {thread_id}")
    print(f"Checkpoint DB: {Path(args.checkpoint_db)}")
    print(f"Memory enabled: {args.memory}")

    checkpoint_path = Path(args.checkpoint_db)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpointer = create_checkpointer(checkpoint_path)
    checkpointer.setup()
    graph = build_application_graph(
        checkpointer=checkpointer,
        enable_default_memory=args.memory,
    )

    initial_state: dict[str, Any] = {"ticker": ticker, "user_query": query}
    if args.eps is not None:
        initial_state["valuation_inputs"] = ValuationInputs(earnings_per_share=args.eps)
        initial_state["valuation_assumptions"] = ValuationAssumptions(
            multiple=args.multiple,
            rationale=args.rationale,
        )

    print("\nSubmitting initial request to the production graph...")
    first_result = graph.invoke(initial_state, config=config)
    _print_json("After initial invocation", _checkpoint_summary(graph, config))

    interrupts = first_result.get("__interrupt__", ())
    if not interrupts:
        _print_json("Unexpected initial terminal result", first_result)
        return 1
    _print_json("Approval interrupt", [item.value for item in interrupts])

    reason = args.reason or (
        "Approved by Lesson 8 smoke test."
        if args.approval == "approve"
        else "Rejected by Lesson 8 smoke test."
    )
    approval_payload = {"decision": args.approval, "reason": reason}
    print(f"\nResuming the same thread with decision={args.approval!r}...")
    final_result = graph.invoke(Command(resume=approval_payload), config=config)

    _print_json("Final checkpoint", _checkpoint_summary(graph, config))
    _print_json(
        "Terminal application result",
        {
            "ticker": final_result.get("ticker"),
            "approval_status": final_result.get("approval_status"),
            "execution_status": final_result.get("execution_status"),
            "research_data_status": final_result.get("research_data_status"),
            "failed_research_areas": final_result.get("failed_research_areas"),
            "degraded_research_areas": final_result.get("degraded_research_areas"),
            "stage_errors": final_result.get("stage_errors"),
            "error_details": final_result.get("error_details"),
            "application_error": final_result.get("application_error"),
            "memory_capture_decision": final_result.get("memory_capture_decision"),
        },
    )

    report_markdown = final_result.get("report_markdown")
    if report_markdown:
        print("\n=== Final report Markdown ===")
        print(report_markdown)

    status = final_result.get("execution_status")
    if status == "completed":
        print("\nRESULT: PASS — production graph completed.")
        return 0
    if status == "rejected":
        print("\nRESULT: PASS — approval rejection reached a clean terminal state.")
        return 0
    print("\nRESULT: FAIL — production graph reached a failed terminal state.")
    return 0 if args.allow_failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
