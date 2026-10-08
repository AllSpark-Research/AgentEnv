from __future__ import annotations

import os
import re
from copy import deepcopy
from typing import Any

from openai import AsyncOpenAI

DEFAULT_MAX_TOKENS = 65536
TRUNCATED_RESPONSE_PLACEHOLDER = "[Response truncated due to length limit]"
_THINK_SPLIT_RE = re.compile("^\\s*(?:<think>)?(.*?)</think>\\s*(.*)$", re.DOTALL)


def is_context_overflow_error(exc: Exception) -> bool:
    body = getattr(exc, "body", None)
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        body = body["error"]
    code = str(body.get("code", "") if isinstance(body, dict) else getattr(exc, "code", "")).lower()
    if code in {
        "context_length_exceeded",
        "context_window_exceeded",
        "max_context_length_exceeded",
        "prompt_too_long",
        "input_too_long",
    }:
        return True
    status = getattr(exc, "status_code", None)
    message = str(body.get("message", str(exc)) if isinstance(body, dict) else exc).lower()
    if status is None:
        match = re.search("http\\s+(\\d{3})", message)
        status = int(match.group(1)) if match else None
    if status in {401, 403, 408, 409, 429}:
        return False
    return any(
        (
            term in message
            for term in (
                "context length",
                "context_length",
                "context window",
                "maximum context",
                "input is too long",
                "prompt is too long",
            )
        )
    ) or bool(
        re.search(
            "(?:input|prompt)(?:.{0,80})(?:token count exceeds|exceeds (?:the )?maximum|too many tokens)", message
        )
    )


class ModelClient:
    def __init__(self, config: dict):
        self.config = config
        self.model = config["name"]
        self.default_extra_body = config.get("extra_body", {})
        self._openai_client = AsyncOpenAI(
            base_url=os.environ.get("MODEL_BASE_URL") or config["base_url"],
            api_key=os.environ.get("MODEL_API_KEY") or "EMPTY",
            timeout=config.get("timeout_seconds", 600),
            max_retries=config.get("max_retries", 2),
        )

    async def aclose(self):
        await self._openai_client.close()

    def _prepare_messages(self, messages: list[dict]) -> list[dict]:
        out: list[dict] = []
        for m in messages:
            new_m = {k: v for k, v in m.items() if not k.startswith("_")}
            if new_m.get("role") == "assistant":
                rc = m.get("_reasoning_content")
                if rc:
                    new_m["reasoning_content"] = rc
            out.append(new_m)
        return out

    async def chat(self, messages: list[dict], *, tools=None, tool_choice=None, max_tokens=None) -> dict:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": self._prepare_messages(messages),
            "temperature": self.config.get("temperature", 1.0),
            "top_p": self.config.get("top_p", 0.95),
            "max_tokens": self.config.get("max_tokens", DEFAULT_MAX_TOKENS) if max_tokens is None else max_tokens,
            "extra_body": deepcopy(self.default_extra_body),
        }
        if tools:
            kwargs["tools"] = tools
            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice
        resp = await self._openai_client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        msg = choice.message
        finish_reason = choice.finish_reason
        content = msg.content
        tool_calls_raw = getattr(msg, "tool_calls", None)
        reasoning_content: str | None = getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None)
        if not reasoning_content:
            extras = getattr(msg, "model_extra", None) or {}
            reasoning_content = extras.get("reasoning_content") or extras.get("reasoning")
        if reasoning_content is not None and (not str(reasoning_content).strip()):
            reasoning_content = None
        if not reasoning_content and content:
            text = str(content)
            if "</think>" in text:
                m = _THINK_SPLIT_RE.match(text)
                if m:
                    rc = m.group(1).strip()
                    reasoning_content = rc or None
                    content = m.group(2)
            elif finish_reason == "length" and (not tool_calls_raw):
                reasoning_content = text.strip() or None
                content = ""
        if finish_reason == "length" and (content is None or not str(content).strip()) and (not tool_calls_raw):
            content = TRUNCATED_RESPONSE_PLACEHOLDER
        result: dict[str, Any] = {
            "role": "assistant",
            "content": content,
            "reasoning_content": reasoning_content,
            "finish_reason": finish_reason,
            "tool_calls": None,
        }
        if tool_calls_raw:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in tool_calls_raw
            ]
        try:
            result["usage"] = resp.usage.model_dump() if resp.usage else None
        except Exception:
            result["usage"] = None
        return result
