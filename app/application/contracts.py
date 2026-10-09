"""Runtime validation helpers for Application stage boundaries."""

from collections.abc import Mapping
from typing import Any


class StageContractError(ValueError):
    """Raised when a subgraph violates its declared output contract."""


def normalize_stage_output(
    payload: Any,
    *,
    stage_name: str,
    result_key: str,
    error_key: str,
) -> dict[str, Any]:
    """Validate a result/error pair and normalize its error to a string.

    A successful stage must return a non-None result and an empty/None error.
    A failed stage must return no result and a non-empty string error. The
    returned mapping always uses an empty string for success and a non-empty
    string for failure, independent of a legacy subgraph's ``None`` convention.
    """

    if not isinstance(payload, Mapping):
        raise StageContractError(
            f"{stage_name} output must be a mapping; "
            f"received {type(payload).__name__}."
        )

    missing = [key for key in (result_key, error_key) if key not in payload]
    if missing:
        raise StageContractError(
            f"{stage_name} output is missing required key(s): "
            f"{', '.join(missing)}."
        )

    result = payload[result_key]
    error = payload[error_key]

    if error is None:
        normalized_error = ""
    elif isinstance(error, str):
        normalized_error = error.strip()
    else:
        raise StageContractError(
            f"{stage_name} field '{error_key}' must be a string or None; "
            f"received {type(error).__name__}."
        )

    if result is not None and normalized_error:
        raise StageContractError(
            f"{stage_name} returned both a result and an error."
        )

    if result is None and not normalized_error:
        raise StageContractError(
            f"{stage_name} returned neither a result nor an error."
        )

    return {result_key: result, error_key: normalized_error}


def validate_ticker_consistency(ticker: str, **results: Any) -> None:
    """Ensure all supplied domain results belong to the requested ticker.

    ``None`` results are ignored so this helper can validate partially
    completed state without treating not-yet-run stages as failures.
    """

    if not isinstance(ticker, str) or not ticker.strip():
        raise StageContractError("Application ticker must be a non-empty string.")

    mismatches: dict[str, str] = {}
    for result_name, result in results.items():
        if result is None:
            continue
        result_ticker = getattr(result, "ticker", None)
        if not isinstance(result_ticker, str) or not result_ticker.strip():
            raise StageContractError(
                f"{result_name} must expose a non-empty ticker field."
            )
        if result_ticker != ticker:
            mismatches[result_name] = result_ticker

    if mismatches:
        details = ", ".join(
            f"{name}={result_ticker}" for name, result_ticker in mismatches.items()
        )
        raise StageContractError(
            f"All Application results must use ticker '{ticker}'. "
            f"Mismatched results: {details}."
        )


def normalize_valuation_output(payload: Any) -> dict[str, Any]:
    """Map the valuation subgraph's legacy result key to the Application key."""

    normalized = normalize_stage_output(
        payload,
        stage_name="Valuation",
        result_key="valuation_analysis",
        error_key="valuation_error",
    )
    return {
        "valuation": normalized["valuation_analysis"],
        "valuation_error": normalized["valuation_error"],
    }
