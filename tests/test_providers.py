"""Adapters are tested against fake clients. No network, no keys."""

from types import SimpleNamespace as NS

import pytest

from modegrid.providers import AnthropicAdapter, OpenAICompatibleAdapter, with_retries


class FakeStream:
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.msg


class FakeAnthropic:
    def __init__(self):
        self.calls = []
        msg = NS(
            content=[NS(type="thinking", thinking=""), NS(type="text", text="final answer")],
            model="claude-sonnet-5",
            stop_reason="end_turn",
            usage=NS(input_tokens=10, output_tokens=20),
        )
        self.messages = NS(stream=lambda **kw: (self.calls.append(kw), FakeStream(msg))[1])


def test_anthropic_adapter_sends_mode_params_and_reads_text():
    fake = FakeAnthropic()
    params = {"thinking": {"type": "disabled"}}
    comp = AnthropicAdapter(client=fake).complete("hi", "claude-sonnet-5", params, 1000)
    assert comp.text == "final answer"
    assert comp.reasoning is None
    assert fake.calls[0]["extra_body"] == params
    assert fake.calls[0]["max_tokens"] == 1000


def test_openai_adapter_moves_token_field_and_reads_reasoning():
    calls = []
    resp = NS(
        choices=[NS(message=NS(content="ans", reasoning_content="trace"), finish_reason="stop")],
        model="m-returned",
        usage=NS(prompt_tokens=1, completion_tokens=2, completion_tokens_details=NS(reasoning_tokens=1)),
    )
    client = NS(chat=NS(completions=NS(create=lambda **kw: (calls.append(kw), resp)[1])))
    comp = OpenAICompatibleAdapter(None, None, client=client).complete(
        "hi", "m", {"_token_field": "max_completion_tokens", "reasoning_effort": "high"}, 500
    )
    assert calls[0]["extra_body"] == {"max_completion_tokens": 500, "reasoning_effort": "high"}
    assert comp.reasoning == "trace" and comp.model_returned == "m-returned"
    assert comp.usage["reasoning_tokens"] == 1


def test_retries_transient_then_succeeds(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        if state["n"] < 3:
            err = RuntimeError("rate limited")
            err.status_code = 429
            raise err
        return "ok"

    assert with_retries(flaky) == "ok"


def test_does_not_retry_client_errors(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    err = RuntimeError("bad request")
    err.status_code = 400
    state = {"n": 0}

    def bad():
        state["n"] += 1
        raise err

    with pytest.raises(RuntimeError):
        with_retries(bad)
    assert state["n"] == 1


def test_openai_adapter_streams_and_reassembles():
    calls = []

    def chunk(content=None, reasoning=None, finish=None, usage=None):
        choices = [] if usage else [NS(delta=NS(content=content, reasoning_content=reasoning), finish_reason=finish)]
        return NS(model="qwen-returned", choices=choices, usage=usage)

    chunks = [
        chunk(reasoning="think "),
        chunk(reasoning="more"),
        chunk(content="final "),
        chunk(content="answer", finish="stop"),
        chunk(usage=NS(prompt_tokens=5, completion_tokens=9, completion_tokens_details=NS(reasoning_tokens=4))),
    ]
    client = NS(chat=NS(completions=NS(create=lambda **kw: (calls.append(kw), iter(chunks))[1])))
    comp = OpenAICompatibleAdapter(None, None, client=client).complete(
        "hi", "qwen3.7-plus", {"_stream": True, "enable_thinking": True}, 100
    )
    assert calls[0]["stream"] is True
    assert "_stream" not in calls[0]["extra_body"]
    assert calls[0]["extra_body"] == {"max_tokens": 100, "enable_thinking": True}
    assert comp.text == "final answer"
    assert comp.reasoning == "think more"
    assert comp.finish_reason == "stop"
    assert comp.usage == {"input_tokens": 5, "output_tokens": 9, "reasoning_tokens": 4}
