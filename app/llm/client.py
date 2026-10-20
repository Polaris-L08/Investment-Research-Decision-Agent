"""Shared LLM client with a bounded provider-level retry policy.

Retry ownership intentionally stays in the OpenAI SDK used by ChatOpenAI.
Application/Graph code must not wrap every LLM invocation in another generic
retry loop; doing so can multiply attempts and repeat tool or workflow effects.
"""
import math
import os
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

DEFAULT_LLM_REQUEST_TIMEOUT_SECONDS = 30.0

# OpenAI SDK semantics: retries AFTER the initial request.
# 2 retries => at most 3 HTTP request attempts for retryable SDK failures.
LLM_MAX_RETRIES = 2


def llm_request_timeout_seconds() -> float:
    """Read and validate the per-request LLM HTTP timeout."""
    raw = os.getenv("LLM_REQUEST_TIMEOUT_SECONDS")
    if raw is None or not raw.strip():
        return DEFAULT_LLM_REQUEST_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(
            "LLM_REQUEST_TIMEOUT_SECONDS must be a positive number of seconds."
        ) from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(
            "LLM_REQUEST_TIMEOUT_SECONDS must be a finite number greater than zero."
        )
    return value


def build_llm(*, http_client: Any | None = None) -> ChatOpenAI:
    """Build the shared model client with bounded SDK retries and request timeout.

    ``timeout`` is passed to ChatOpenAI's client configuration, not to
    ``Runnable.invoke`` kwargs. It bounds an individual HTTP request; retries
    are separately bounded by ``LLM_MAX_RETRIES``.
    """
    client_options: dict[str, Any] = {
        "model": os.getenv("LLM_MODEL"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "temperature": 0,
        "timeout": llm_request_timeout_seconds(),
        "max_retries": LLM_MAX_RETRIES,
        "extra_body": {
            "thinking": {
                "type": "disabled"  # 关键：关闭思考模式
            }
        },
    }
    if http_client is not None:
        client_options["http_client"] = http_client
    return ChatOpenAI(**client_options)


llm = build_llm()
