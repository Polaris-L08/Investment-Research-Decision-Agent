"""Small subprocess boundary for synchronous SDK calls without native timeouts.

The worker protocol is deliberately simple: JSON goes to stdin, and the SDK
adapter's script writes a result marker to stdout. A subprocess can be killed
on timeout; a thread timeout cannot stop an arbitrary synchronous SDK call.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from typing import Any

from app.providers.config import ProviderConfigurationError


DEFAULT_PROVIDER_SDK_TIMEOUT_SECONDS = 30.0


def provider_sdk_timeout_seconds() -> float:
    """Return the positive timeout used for isolated third-party SDK calls."""
    raw = os.getenv("PROVIDER_SDK_TIMEOUT_SECONDS")
    if raw is None or not raw.strip():
        return DEFAULT_PROVIDER_SDK_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError as exc:
        raise ProviderConfigurationError(
            "PROVIDER_SDK_TIMEOUT_SECONDS must be a positive number of seconds."
        ) from exc
    if not math.isfinite(value) or value <= 0:
        raise ProviderConfigurationError(
            "PROVIDER_SDK_TIMEOUT_SECONDS must be a finite number greater than zero."
        )
    return value


def run_isolated_python_json(
    *,
    script: str,
    payload: dict[str, Any],
    timeout_seconds: float,
    operation_name: str,
) -> tuple[int, str, str]:
    """Run a JSON-in/JSON-out Python worker with a real process timeout.

    The worker is killed on timeout or if cancellation/interrupt propagates
    through this call. This does not claim to terminate unrelated child
    processes that the SDK itself may spawn.
    """
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a finite number greater than zero.")

    input_text = json.dumps(payload, ensure_ascii=False, default=str)
    process = subprocess.Popen(
        [sys.executable, "-c", script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        try:
            stdout, stderr = process.communicate(
                input=input_text,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            if process.poll() is None:
                try:
                    process.kill()
                except OSError:
                    pass
            process.communicate()
            raise TimeoutError(
                f"{operation_name} exceeded its {timeout_seconds:g}-second timeout."
            ) from exc
    except BaseException:
        if process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass
        process.communicate()
        raise

    return (process.returncode if process.returncode is not None else 0), stdout, stderr
