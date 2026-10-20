"""Structured error taxonomy for the production Application boundary.

This module classifies errors; it does not execute retries or choose fallbacks.
Those policies belong to later Error Recovery lessons.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from app.application.contracts import StageContractError
from app.providers.config import ProviderConfigurationError
from app.providers.exceptions import TransientProviderError


ErrorCategory = Literal[
    "transient_provider",
    "provider_configuration",
    "timeout",
    "stage_contract",
    "input_validation",
    "business_input",
    "stage_reported_failure",
    "unexpected",
]


class ApplicationErrorDetail(TypedDict):
    """Stable, serializable diagnostic record for one failed boundary."""

    stage: str
    code: str
    category: ErrorCategory
    retryable: bool | None
    handling_owner: str
    exception_type: str
    message: str


def classify_exception(exc: Exception) -> dict[str, object]:
    """Classify an exception without assuming every error is retryable.

    ``retryable=None`` means the taxonomy alone cannot decide. A later policy
    must consider operation semantics, remaining budget, and side effects.
    """

    if isinstance(exc, TransientProviderError):
        return {
            "code": "TRANSIENT_PROVIDER_FAILURE",
            "category": "transient_provider",
            "retryable": True,
            "handling_owner": "provider_retry_policy",
        }
    if isinstance(exc, ProviderConfigurationError):
        return {
            "code": "PROVIDER_CONFIGURATION_ERROR",
            "category": "provider_configuration",
            "retryable": False,
            "handling_owner": "provider_configuration_boundary",
        }
    if isinstance(exc, TimeoutError):
        return {
            "code": "OPERATION_TIMEOUT",
            "category": "timeout",
            "retryable": None,
            "handling_owner": "retry_and_deadline_policy",
        }
    if isinstance(exc, StageContractError):
        return {
            "code": "STAGE_CONTRACT_VIOLATION",
            "category": "stage_contract",
            "retryable": False,
            "handling_owner": "application_stage_boundary",
        }
    return {
        "code": "UNCLASSIFIED_EXCEPTION",
        "category": "unexpected",
        "retryable": None,
        "handling_owner": "application_error_boundary",
    }


def make_error_detail(
    *,
    stage: str,
    message: str,
    exc: Exception | None = None,
    code: str | None = None,
    category: ErrorCategory | None = None,
    retryable: bool | None = None,
    handling_owner: str | None = None,
) -> ApplicationErrorDetail:
    """Build a structured record while retaining the available exception type."""

    if exc is not None:
        classification = classify_exception(exc)
        error_type = type(exc).__name__
        normalized_message = str(exc).strip() or error_type
    else:
        # A string reported by a child graph is not enough to infer its root
        # exception or retryability. Keep that uncertainty explicit.
        classification = {
            "code": "STAGE_REPORTED_FAILURE",
            "category": "stage_reported_failure",
            "retryable": None,
            "handling_owner": "stage_boundary",
        }
        error_type = ""
        normalized_message = message.strip() or "Stage reported a failure without a message."

    return {
        "stage": stage,
        "code": code or str(classification["code"]),
        "category": category or classification["category"],  # type: ignore[typeddict-item]
        "retryable": retryable if retryable is not None else classification["retryable"],
        "handling_owner": handling_owner or str(classification["handling_owner"]),
        "exception_type": error_type,
        "message": normalized_message,
    }
