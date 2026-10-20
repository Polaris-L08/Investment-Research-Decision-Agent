from app.llm import client as llm_client


def test_llm_retry_policy_allows_two_retries_after_initial_attempt():
    # OpenAI SDK's max_retries excludes the initial request.
    assert llm_client.LLM_MAX_RETRIES == 2
    assert llm_client.LLM_MAX_RETRIES + 1 == 3


def test_build_llm_configures_bounded_retries(monkeypatch):
    captured = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(llm_client, "ChatOpenAI", FakeChatOpenAI)

    result = llm_client.build_llm()

    assert isinstance(result, FakeChatOpenAI)
    assert captured["max_retries"] == 2
    assert captured["temperature"] == 0
    assert "model" in captured
    assert "base_url" in captured