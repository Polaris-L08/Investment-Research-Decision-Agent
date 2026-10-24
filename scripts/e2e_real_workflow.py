"""End-to-end smoke test: real LLM + explicit Mock data providers.

This script invokes the production Application Graph, including the real LLM
agents, SQLite checkpointing, HITL approval/resume, valuation, risk, decision,
and report stages. Market/company/financial inputs come from Mock providers;
this is NOT a live-market-data test.

Example:
    python scripts/e2e_real_workflow.py --allow-paid-llm-calls --ticker AAPL
    python scripts/e2e_real_workflow.py --allow-paid-llm-calls --approve --ticker AAPL

The second command pre-authorizes approval of the HITL gate for unattended runs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# When Python executes a file by path, sys.path[0] is usually the scripts/
# directory rather than the project root. Add the root explicitly so imports
# such as `from app...` work regardless of the caller's working directory.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_QUERY_TEMPLATE = (
    "请基于当前工作流提供的研究输入，完成 {ticker} 的公司基本面、财务、"
    "市场表现、行业与宏观研究，并在完成估值、风险分析和投资决策后生成"
    "结构完整的投资研究报告。请明确区分事实、假设和不确定性，不要把"
    "Mock 数据描述为真实实时行情或已核验的外部事实。"
)


class E2EAcceptanceError(RuntimeError):
    """Raised when the workflow does not satisfy the E2E acceptance contract."""


def _json_default(value: Any) -> Any:
    """Serialize Pydantic models and enums without hiding unsupported objects."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return repr(value)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the production Application Graph with a real LLM and explicit "
            "Mock data providers. Real LLM API usage may incur charges."
        )
    )
    parser.add_argument("--ticker", default="AAPL", help="Ticker supported by the Mock fixtures (default: AAPL).")
    parser.add_argument(
        "--query",
        default=None,
        help="Optional research request. A safe default is generated when omitted.",
    )
    parser.add_argument(
        "--allow-paid-llm-calls",
        action="store_true",
        help="Explicitly authorize real LLM API calls; without this flag, the script exits before invoking the model.",
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Explicitly approve the workflow's HITL gate without an interactive prompt.",
    )
    parser.add_argument(
        "--approval-reason",
        default="Explicit approval supplied for the E2E acceptance run.",
        help="Reason recorded when --approve is supplied.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Artifact directory. Defaults to artifacts/e2e/<ticker>-<UTC timestamp>-<run id>.",
    )
    return parser.parse_args()


def _validate_configuration(args: argparse.Namespace) -> tuple[str, str]:
    if not args.allow_paid_llm_calls:
        raise E2EAcceptanceError(
            "Refusing to call the real LLM without explicit authorization. "
            "Re-run with --allow-paid-llm-calls after confirming potential API costs."
        )

    ticker = args.ticker.strip().upper()
    if not re.fullmatch(r"[A-Z0-9.^=_-]{1,20}", ticker):
        raise E2EAcceptanceError(
            "Ticker must be 1-20 characters and contain only letters, digits, '.', '^', '=', '_' or '-'."
        )

    # Load .env before checking credentials. Do not print secrets.
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    app_env = os.getenv("APP_ENV", "development").strip().lower()
    if app_env == "production":
        raise E2EAcceptanceError(
            "This acceptance script uses Mock providers and is prohibited when APP_ENV=production. "
            "Use a dedicated development/test environment."
        )

    model = (os.getenv("LLM_MODEL") or "").strip()
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not model:
        raise E2EAcceptanceError("LLM_MODEL is missing. Configure it in .env or the environment.")
    if not api_key:
        raise E2EAcceptanceError("OPENAI_API_KEY is missing. Configure it in .env or the environment.")

    # Config A intentionally chooses Mock data providers even if .env currently
    # selects real providers. This is explicit, visible, and occurs before app
    # modules (which construct global provider/LLM objects) are imported.
    os.environ["APP_ENV"] = app_env or "development"
    os.environ["PROVIDER_MODE"] = "mock"

    return ticker, model


def _acceptance_checks(result: dict[str, Any], ticker: str) -> list[str]:
    """Raise on contract violations; return the successful checks for artifacts."""
    checks: list[str] = []

    if result.get("ticker") != ticker:
        raise E2EAcceptanceError(
            f"Output ticker mismatch: expected {ticker!r}, got {result.get('ticker')!r}."
        )
    checks.append("output ticker matches request")

    if result.get("approval_status") != "approved":
        raise E2EAcceptanceError(
            f"HITL approval did not finish as approved: {result.get('approval_status')!r}."
        )
    checks.append("HITL approval accepted")

    if result.get("execution_status") != "completed":
        raise E2EAcceptanceError(
            "Application workflow did not complete successfully: "
            f"execution_status={result.get('execution_status')!r}, "
            f"application_error={result.get('application_error')!r}, "
            f"stage_errors={result.get('stage_errors')!r}."
        )
    checks.append("terminal execution status is completed")

    required_objects = (
        "company_research",
        "financial_research",
        "market_research",
        "industry_macro_research",
        "valuation",
        "risk_analysis",
        "investment_decision",
        "report",
    )
    missing = [name for name in required_objects if result.get(name) is None]
    if missing:
        raise E2EAcceptanceError(f"Required workflow outputs are missing: {missing}.")
    checks.append("all four research results and downstream domain objects are present")

    if result.get("stage_errors"):
        raise E2EAcceptanceError(f"stage_errors is not empty: {result['stage_errors']!r}")
    if result.get("error_details"):
        raise E2EAcceptanceError(f"error_details is not empty: {result['error_details']!r}")
    if result.get("application_error"):
        raise E2EAcceptanceError(f"application_error is not empty: {result['application_error']!r}")
    checks.append("application and structured error collections are empty")

    report = result["report"]
    report_ticker = getattr(report, "ticker", None)
    if report_ticker != ticker:
        raise E2EAcceptanceError(
            f"Report ticker mismatch: expected {ticker!r}, got {report_ticker!r}."
        )
    checks.append("structured report ticker matches request")

    markdown = result.get("report_markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        raise E2EAcceptanceError("Final report_markdown is empty.")
    checks.append("non-empty Markdown report generated")

    # Config A's data source is deliberately Mock; do not claim that this run
    # validates live-data freshness or source coverage.
    checks.append("data-provider mode explicitly configured as mock")
    return checks


def main() -> int:
    args = _parse_args()
    run_id = uuid.uuid4().hex[:12]
    started_at = datetime.now(timezone.utc)

    try:
        ticker, model = _validate_configuration(args)
    except E2EAcceptanceError as exc:
        print(f"[PRECHECK FAILED] {exc}", file=sys.stderr)
        return 2

    timestamp = started_at.strftime("%Y%m%dT%H%M%SZ")
    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    else:
        output_dir = PROJECT_ROOT / "artifacts" / "e2e" / f"{ticker}-{timestamp}-{run_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Isolate both workflow checkpoints and long-term memory artifacts from the
    # application's default data directory.
    checkpoint_path = output_dir / "checkpoints.sqlite"
    os.environ["MEMORY_DATABASE_PATH"] = str(output_dir / "memory.sqlite3")

    thread_id = f"e2e-{ticker.lower()}-{run_id}"
    query = args.query.strip() if args.query and args.query.strip() else DEFAULT_QUERY_TEMPLATE.format(ticker=ticker)

    metadata: dict[str, Any] = {
        "run_id": run_id,
        "thread_id": thread_id,
        "ticker": ticker,
        "started_at_utc": started_at.isoformat(),
        "llm_model": model,
        "provider_mode": "mock",
        "test_profile": "real_llm_mock_data_providers_production_application_graph",
        "live_market_data_validated": False,
        "approval_mode": "preapproved_cli_flag" if args.approve else "interactive",
        "artifacts": {
            "summary": str(output_dir / "run_summary.json"),
            "result": str(output_dir / "result.json"),
            "report": str(output_dir / "report.md"),
            "checkpoints": str(checkpoint_path),
        },
    }
    _write_json(output_dir / "run_metadata.json", metadata)

    checkpointer = None
    connection = None
    try:
        # Imports happen only after PROVIDER_MODE is explicitly set, because
        # the provider bundle and shared LLM client are initialized at import.
        from langgraph.types import Command

        from app.graph.checkpointer import create_checkpointer
        from app.graph.runtime import build_thread_config, create_application_graph
        from app.providers.runtime import get_provider_bundle

        bundle = get_provider_bundle()
        if bundle.mode != "mock":
            raise E2EAcceptanceError(
                f"Provider bundle is not Mock as required; actual mode={bundle.mode!r}."
            )

        checkpointer = create_checkpointer(checkpoint_path)
        # SqliteSaver.setup() is required to initialize checkpoint tables.
        checkpointer.setup()
        connection = getattr(checkpointer, "conn", None)
        graph = create_application_graph(checkpointer=checkpointer)
        config = build_thread_config(thread_id)

        print("=== E2E Acceptance Run ===")
        print(f"Ticker: {ticker}")
        print(f"LLM model: {model}")
        print("Data providers: MOCK (live market data is NOT being tested)")
        print(f"Thread ID: {thread_id}")
        print(f"Artifacts: {output_dir}")
        print("Starting production Application Graph; waiting for HITL interrupt...")

        initial_result = graph.invoke(
            {"ticker": ticker, "user_query": query},
            config=config,
        )
        interrupts = initial_result.get("__interrupt__", ())
        if not interrupts:
            _write_json(output_dir / "initial_result.json", initial_result)
            raise E2EAcceptanceError(
                "Expected the production graph to pause at the HITL approval gate, "
                "but no interrupt was returned."
            )

        interrupt_payloads = [
            getattr(item, "value", repr(item))
            for item in interrupts
        ]
        _write_json(output_dir / "hitl_interrupt.json", interrupt_payloads)
        print("HITL interrupt received and recorded.")

        if args.approve:
            decision = "approve"
            reason = args.approval_reason.strip() or "Explicit E2E approval."
        else:
            if not sys.stdin.isatty():
                raise E2EAcceptanceError(
                    "No interactive terminal is available to answer HITL approval. "
                    "Re-run with --approve to explicitly authorize approval."
                )
            answer = input("Approve this E2E research run and continue to real LLM calls? [y/N]: ").strip().lower()
            if answer not in {"y", "yes"}:
                print("Approval not granted; the workflow remains paused at the HITL gate.")
                summary = {
                    **metadata,
                    "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                    "outcome": "paused_pending_approval",
                    "checks": ["HITL interrupt received"],
                    "error": "",
                }
                _write_json(output_dir / "run_summary.json", summary)
                return 3
            decision = "approve"
            reason = "Human approved interactively for the E2E acceptance run."

        final_result = graph.invoke(
            Command(resume={"decision": decision, "reason": reason}),
            config=config,
        )

        # Save outputs before assertions so failures remain diagnosable.
        _write_json(output_dir / "result.json", final_result)
        report_markdown = final_result.get("report_markdown")
        if isinstance(report_markdown, str):
            (output_dir / "report.md").write_text(report_markdown, encoding="utf-8")

        checks = _acceptance_checks(final_result, ticker)
        finished_at = datetime.now(timezone.utc)
        summary = {
            **metadata,
            "finished_at_utc": finished_at.isoformat(),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
            "outcome": "passed",
            "checks": checks,
            "execution_status": final_result.get("execution_status"),
            "approval_status": final_result.get("approval_status"),
            "research_data_status": final_result.get("research_data_status"),
            "degraded_research_areas": final_result.get("degraded_research_areas", []),
            "memory_capture_decision": final_result.get("memory_capture_decision"),
            "memory_capture_reason": final_result.get("memory_capture_reason"),
            "error": "",
        }
        _write_json(output_dir / "run_summary.json", summary)

        print("\n[PASS] End-to-end workflow completed.")
        for check in checks:
            print(f"  - {check}")
        print(f"Report: {output_dir / 'report.md'}")
        print(f"Summary: {output_dir / 'run_summary.json'}")
        return 0

    except Exception as exc:
        failure = {
            **metadata,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "outcome": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        _write_json(output_dir / "failure_diagnostics.json", failure)
        _write_json(
            output_dir / "run_summary.json",
            {
                **metadata,
                "finished_at_utc": failure["finished_at_utc"],
                "outcome": "failed",
                "error_type": failure["error_type"],
                "error": failure["error"],
            },
        )
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"Diagnostics: {output_dir / 'failure_diagnostics.json'}", file=sys.stderr)
        return 1
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        elif checkpointer is not None:
            try:
                checkpointer.conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
