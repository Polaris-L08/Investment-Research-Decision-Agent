
"""Shared input/output helpers for Research child-agent graphs."""

from typing import Any, TypeVar

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