
"""Shared input/output helpers for Research child-agent graphs."""
import json
import math
from typing import Any, TypeVar, Mapping

from pydantic import BaseModel


ResearchResultT = TypeVar("ResearchResultT", bound=BaseModel)


def require_research_result(
    result: Any,
    expected_type: type[ResearchResultT],
) -> ResearchResultT:
    """Reject missing or incorrectly typed structured research results."""

    if not isinstance(result, expected_type):
        raise TypeError(
            "Research agent returned an invalid structured result: "
            f"expected {expected_type.__name__}, "
            f"received {type(result).__name__}."
        )

    return result


def mark_research_complete(result: ResearchResultT) -> ResearchResultT:
    """Mark a normally synthesized result complete, overriding LLM metadata."""

    if not isinstance(result, BaseModel):
        raise TypeError("Research completion metadata requires a Pydantic result.")
    fields = getattr(type(result), "model_fields", {})
    if "data_status" not in fields or "degradation_reason" not in fields:
        raise TypeError("Research result is missing the shared degradation contract.")
    return result.model_copy(update={"data_status": "complete", "degradation_reason": ""})


def parse_tool_payloads_by_name(
    tool_result: Mapping[str, Any],
    *,
    allowed_names: set[str],
) -> dict[str, Any]:
    """Parse successful tool messages, preserving each registered tool's identity.

    Tool outputs are JSON-decoded because LangChain ToolMessage content may
    represent either a JSON object or a JSON scalar (for example a float).
    Failed tool messages and malformed payloads are intentionally ignored; the
    fallback builder then fails closed if any required evidence is absent.
    """
    messages = tool_result.get("messages")
    if not isinstance(messages, list):
        raise ValueError("Research tool output has no messages list.")

    names_by_call_id: dict[str, str] = {}
    for message in messages:
        for call in getattr(message, "tool_calls", []) or []:
            call_id = call.get("id")
            name = call.get("name")
            if isinstance(call_id, str) and isinstance(name, str):
                names_by_call_id[call_id] = name

    payloads: dict[str, Any] = {}
    for message in messages:
        if getattr(message, "type", None) != "tool":
            continue
        if getattr(message, "status", "success") == "error":
            continue

        name = getattr(message, "name", None)
        if not isinstance(name, str) or not name:
            name = names_by_call_id.get(getattr(message, "tool_call_id", ""))
        if name not in allowed_names:
            continue

        content = getattr(message, "content", None)
        if not isinstance(content, str):
            continue
        try:
            payload = json.loads(content)
        except (TypeError, json.JSONDecodeError):
            continue
        payloads[name] = payload

    return payloads


def require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Fallback requires a non-empty {field_name}.")
    return value.strip()


def require_finite_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Fallback requires a numeric {field_name}.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Fallback requires a finite {field_name}.")
    return number


def require_matching_ticker(payload: Any, ticker: str, field_name: str) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError(f"Fallback {field_name} output must be an object.")
    actual = payload.get("ticker")
    if not isinstance(actual, str) or actual.strip().upper() != ticker.strip().upper():
        raise ValueError(f"Fallback {field_name} output does not match the requested ticker.")



def require_tool_calls_match_ticker(
    tool_result: Mapping[str, Any], ticker: str, required_names: set[str]
) -> None:
    """Ensure required tool calls were explicitly issued for the requested ticker."""
    messages = tool_result.get("messages")
    if not isinstance(messages, list):
        raise ValueError("Research tool output has no messages list.")
    calls_by_name: dict[str, list[Any]] = {}
    for message in messages:
        for call in getattr(message, "tool_calls", []) or []:
            name = call.get("name")
            if isinstance(name, str):
                calls_by_name.setdefault(name, []).append(call.get("args"))
    requested = ticker.strip().upper()
    for name in required_names:
        calls = calls_by_name.get(name, [])
        if not calls:
            raise ValueError(f"Fallback has no recorded call for required tool '{name}'.")
        if not all(
            isinstance(args, Mapping)
            and isinstance(args.get("ticker"), str)
            and args["ticker"].strip().upper() == requested
            for args in calls
        ):
            raise ValueError(
                f"Fallback tool call '{name}' does not match the requested ticker."
            )


def is_timeout_failure(error: BaseException) -> bool:
    """Recognize timeout errors so a fallback cannot bypass execution deadlines."""
    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, TimeoutError) or "timeout" in type(current).__name__.lower():
            return True
        current = current.__cause__ or current.__context__
    return False

def research_success(result: ResearchResultT) -> dict[str, Any]:
    """Build the standard success payload used by every Research child."""

    if not isinstance(result, BaseModel):
        raise TypeError(
            "Research success payload requires a validated Pydantic result; "
            f"received {type(result).__name__}."
        )

    return {
        "research_result": result,
        "research_error": "",
    }


def research_failure(error: Exception) -> dict[str, Any]:
    """Build the standard failure payload, including a useful fallback."""

    message = str(error).strip() or type(error).__name__

    return {
        "research_result": None,
        "research_error": message,
    }