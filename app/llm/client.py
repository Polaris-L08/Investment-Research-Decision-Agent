"""Shared LLM client with bounded retries for transient provider failures."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# OpenAI SDK semantics: max_retries is the number of retries after the initial
# request. Thus 2 means at most 3 total attempts. The SDK retries selected
# transient transport/API failures, not arbitrary application exceptions.
LLM_MAX_RETRIES = 2


def build_llm() -> ChatOpenAI:
    """Build the shared model client with a bounded provider retry policy."""
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        temperature=0,
        max_retries=LLM_MAX_RETRIES,
        extra_body={
            "thinking": {
                "type": "disabled"  # 关键：关闭思考模式
            }
        },
    )


llm = build_llm()