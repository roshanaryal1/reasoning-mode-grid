"""Provider adapters. Each turns (prompt, model, mode params) into one Completion.

Design rules:

* Mode parameters live in configs/grid.yaml, not in code. Vendor APIs change the
  way reasoning is switched on and off. When that happens you edit YAML, the code
  stays put, and the change is visible in the config diff.
* Mode params are sent as `extra_body`, so a new vendor field does not need an
  SDK upgrade to reach the wire.
* No silent fallbacks. If a vendor refuses or swaps the model, the capture
  records it. A server-side model fallback would put the wrong model in a cell.
* SDKs are imported lazily so the analysis side installs without them.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from .config import Family


@dataclass
class Completion:
    text: str
    reasoning: str | None
    model_returned: str
    finish_reason: str | None
    usage: dict[str, int | None] = field(default_factory=dict)
    latency_s: float = 0.0


class Adapter(Protocol):
    def complete(self, prompt: str, model: str, params: dict[str, Any], max_tokens: int) -> Completion: ...


class AnthropicAdapter:
    """Claude Messages API through the official `anthropic` SDK, streamed.

    Streaming matters: reasoning-mode answers to the study prompt are long, and a
    non-streamed request with a high max_tokens can hit the HTTP timeout.
    """

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client

    def complete(self, prompt: str, model: str, params: dict[str, Any], max_tokens: int) -> Completion:
        start = time.monotonic()
        with self.client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            extra_body=params,
        ) as stream:
            msg = stream.get_final_message()
        latency = time.monotonic() - start
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        thinking = "".join(
            getattr(b, "thinking", "") or "" for b in msg.content if getattr(b, "type", None) == "thinking"
        )
        usage = msg.usage
        return Completion(
            text=text,
            reasoning=thinking or None,
            model_returned=msg.model,
            finish_reason=msg.stop_reason,
            usage={
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "reasoning_tokens": None,  # included in output_tokens, not reported separately
            },
            latency_s=round(latency, 2),
        )


class OpenAICompatibleAdapter:
    """Any vendor exposing an OpenAI-style /chat/completions endpoint.

    Covers OpenAI itself plus vendors that ship a compatible endpoint (DeepSeek,
    Qwen/DashScope, xAI, Gemini's compatibility layer). Check each vendor's docs:
    the reasoning switch differs per vendor and is set in grid.yaml.
    """

    def __init__(self, base_url: str | None, api_key_env: str | None, client: Any | None = None) -> None:
        if client is None:
            from openai import OpenAI

            if not api_key_env or not os.environ.get(api_key_env):
                raise RuntimeError(f"set {api_key_env} in the environment (see .env.example)")
            client = OpenAI(base_url=base_url, api_key=os.environ[api_key_env], timeout=1800)
        self.client = client

    def complete(self, prompt: str, model: str, params: dict[str, Any], max_tokens: int) -> Completion:
        params = dict(params)
        # Some reasoning models reject max_tokens and want max_completion_tokens.
        # Let the config decide; default to max_tokens.
        token_field = params.pop("_token_field", "max_tokens")
        # Some vendors only return the thinking text when the response is streamed
        # (DashScope documents this for some Qwen models). `_stream: true` in the
        # mode params switches to streaming and reassembles the same Completion.
        if params.pop("_stream", False):
            return self._complete_streamed(prompt, model, params, max_tokens, token_field)
        start = time.monotonic()
        resp = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            extra_body={token_field: max_tokens, **params},
        )
        latency = time.monotonic() - start
        choice = resp.choices[0]
        message = choice.message
        usage = resp.usage
        details = getattr(usage, "completion_tokens_details", None)
        return Completion(
            text=message.content or "",
            reasoning=getattr(message, "reasoning_content", None),
            model_returned=resp.model,
            finish_reason=choice.finish_reason,
            usage={
                "input_tokens": getattr(usage, "prompt_tokens", None),
                "output_tokens": getattr(usage, "completion_tokens", None),
                "reasoning_tokens": getattr(details, "reasoning_tokens", None) if details else None,
            },
            latency_s=round(latency, 2),
        )

    def _complete_streamed(
        self, prompt: str, model: str, params: dict[str, Any], max_tokens: int, token_field: str
    ) -> Completion:
        start = time.monotonic()
        stream = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            stream_options={"include_usage": True},
            extra_body={token_field: max_tokens, **params},
        )
        text: list[str] = []
        reasoning: list[str] = []
        model_returned, finish_reason, usage = model, None, None
        for chunk in stream:
            model_returned = getattr(chunk, "model", None) or model_returned
            if getattr(chunk, "usage", None) is not None:
                usage = chunk.usage
            for choice in getattr(chunk, "choices", None) or []:
                delta = choice.delta
                if getattr(delta, "content", None):
                    text.append(delta.content)
                if getattr(delta, "reasoning_content", None):
                    reasoning.append(delta.reasoning_content)
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
        latency = time.monotonic() - start
        details = getattr(usage, "completion_tokens_details", None) if usage else None
        return Completion(
            text="".join(text),
            reasoning="".join(reasoning) or None,
            model_returned=model_returned,
            finish_reason=finish_reason,
            usage={
                "input_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                "output_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                "reasoning_tokens": getattr(details, "reasoning_tokens", None) if details else None,
            },
            latency_s=round(latency, 2),
        )


def adapter_for(family: Family) -> Adapter:
    if family.adapter == "anthropic":
        return AnthropicAdapter()
    if family.adapter == "openai_compatible":
        return OpenAICompatibleAdapter(family.base_url, family.api_key_env)
    raise ValueError(f"{family.id}: no API adapter for channel={family.channel}, adapter={family.adapter}")


def with_retries(fn: Any, attempts: int = 4, base_delay: float = 2.0) -> Any:
    """Retry transient failures with exponential backoff (2s, 4s, 8s, ...)."""
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            transient = status is None or status == 429 or status >= 500
            if not transient or i == attempts - 1:
                raise
            time.sleep(base_delay * 2**i)
    raise AssertionError("unreachable")
