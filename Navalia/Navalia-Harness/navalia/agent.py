from __future__ import annotations

import hashlib
import json
import re
import time
from collections import deque
from dataclasses import dataclass, field
from itertools import chain
from typing import Any

from .client import ModelClient, is_context_overflow_error
from .file_state_cache import FileStateCache
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .tools import TOOL_SCHEMAS, dispatch_tool

MAX_STEPS = 200
FIFO_MAX_TURNS = 30
FIFO_MIN_TURNS = 20
MAX_REPEATED_CALL = 3
FORCE_FINAL_MAX_TOKENS = 16384
STEP_REMINDER_THRESHOLD = 30


def _extract_final_answer(content: str) -> str | None:
    lower = content.lower()
    end_tag = "</final_answer>"
    start_tag = "<final_answer>"
    end_pos = lower.rfind(end_tag)
    if end_pos == -1:
        return None
    start_pos = lower.rfind(start_tag, 0, end_pos)
    if start_pos == -1:
        return None
    inner = content[start_pos + len(start_tag) : end_pos].strip()
    return inner if inner else None


@dataclass
class TraceStep:
    step: int
    role: str
    content: str | None = None
    tool_calls: list[dict] | None = None
    tool_results: list[dict] | None = None
    usage: dict | None = None
    reasoning_content: str | None = None
    timestamp: float = field(default_factory=time.time)


def _attach_reasoning(msg: dict, reasoning: str | None, *, context_offset: int | None = None) -> dict:
    if context_offset is not None:
        msg["_fifo_context_offset"] = context_offset
    if reasoning:
        msg["_reasoning_content"] = reasoning
    return msg


@dataclass
class AgentResult:
    uid: str
    question: str
    final_answer: str | None
    full_assistant_output: str | None
    steps_used: int
    finish_reason: str
    error: str | None
    trace: list[TraceStep]
    system_prompt: str = ""
    tool_schemas: list[dict] = field(default_factory=list)
    main_agent_message_history: dict = field(default_factory=dict)


def _message_for_history(msg: dict) -> dict:
    out: dict = {"role": msg.get("role")}
    if "content" in msg and msg.get("content") is not None:
        out["content"] = msg["content"]
    if msg.get("tool_calls"):
        out["tool_calls"] = msg["tool_calls"]
    if "tool_call_id" in msg:
        out["tool_call_id"] = msg["tool_call_id"]
    if "name" in msg:
        out["name"] = msg["name"]
    if msg.get("_reasoning_content"):
        out["_reasoning_content"] = msg["_reasoning_content"]
    if "_fifo_context_offset" in msg:
        out["_fifo_context_offset"] = msg["_fifo_context_offset"]
    return out


def _build_main_agent_message_history(system_prompt: str, tool_schemas: list[dict], messages: list[dict]) -> dict:
    body: list[dict] = []
    for m in messages:
        if m.get("role") == "system":
            continue
        body.append(_message_for_history(m))
    return {"system_prompt": system_prompt, "tools": list(tool_schemas), "message_history": body}


def _segment_turns(messages: list[dict]):
    system_msgs = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    turns: list[list[dict]] = []
    current: list[dict] = []
    for m in non_system:
        if m.get("role") == "assistant":
            if current:
                turns.append(current)
            current = [m]
        else:
            current.append(m)
    if current:
        turns.append(current)
    if not turns:
        return (system_msgs, None, [])
    first_is_user_init = (
        turns[0] and turns[0][0].get("role") == "user" and all((m.get("role") != "assistant" for m in turns[0]))
    )
    if first_is_user_init:
        return (system_msgs, turns[0], turns[1:])
    return (system_msgs, None, turns)


def _fifo_condense(
    messages: list[dict], offset: int, *, max_turns: int = FIFO_MAX_TURNS, drop: int = FIFO_MAX_TURNS - FIFO_MIN_TURNS
) -> tuple[list[dict], int, int]:
    system_msgs, pinned_turn, assistant_turns = _segment_turns(messages)
    n = len(assistant_turns)
    new_offset = offset
    while n - new_offset > max_turns:
        new_offset += drop
    if new_offset > n:
        new_offset = n
    n_dropped = new_offset - offset
    windowed: list[dict] = list(system_msgs)
    if pinned_turn is not None:
        windowed.extend(pinned_turn)
    for turn in assistant_turns[new_offset:]:
        windowed.extend(turn)
    return (windowed, new_offset, n_dropped)


def _parse_tool_arguments(args_str: str) -> dict:
    if not args_str:
        return {}
    try:
        return json.loads(args_str)
    except Exception:
        m = re.search("\\{[\\s\\S]*\\}", args_str)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return {"_raw": args_str}


def _tool_call_signature(tool_name: str, args: dict) -> str:
    try:
        norm = json.dumps(args, sort_keys=True, ensure_ascii=False)
    except Exception:
        norm = repr(args)
    h = hashlib.sha1(norm.encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"{tool_name}::{h}"


def _trim_last_tool_pair(messages: list[dict]) -> tuple[list[dict], bool]:
    last_asst_with_tools = -1
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if m.get("role") == "assistant" and m.get("tool_calls"):
            last_asst_with_tools = i
            break
    if last_asst_with_tools < 0:
        return (messages, False)
    return (messages[:last_asst_with_tools], True)


async def _force_final_answer(
    llm: ModelClient,
    messages: list[dict],
    *,
    fifo_offset: int,
    fifo_max: int,
    fifo_drop: int,
    why: str,
    verbose: bool = False,
) -> tuple[str | None, str | None, str, str | None]:
    forced_user_prompt = f"[SYSTEM] You have {why}. You cannot use any tools anymore. Based on the information you have gathered so far, output your best-guess final answer NOW, as a single line in the form `<FINAL_ANSWER>your_answer</FINAL_ANSWER>` with no other prose. If you genuinely cannot answer, output `<FINAL_ANSWER>unknown</FINAL_ANSWER>`."
    forced_msgs = list(_fifo_condense(messages, fifo_offset, max_turns=fifo_max, drop=fifo_drop)[0]) + [
        {"role": "user", "content": forced_user_prompt}
    ]
    try:
        resp = await llm.chat(messages=forced_msgs, tools=None, tool_choice=None, max_tokens=FORCE_FINAL_MAX_TOKENS)
    except Exception as e:
        if verbose:
            print(f"  ✖ force-final-answer chat failed: {type(e).__name__}: {e}")
        return (None, f"[force_final_answer error] {type(e).__name__}: {e}", forced_user_prompt, None)
    content = resp.get("content") or ""
    reasoning_content = resp.get("reasoning_content")
    return (_extract_final_answer(content), content, forced_user_prompt, reasoning_content)


async def run_agent(
    llm: ModelClient,
    *,
    uid: str,
    question: str,
    source_files: list[str] | None,
    sandbox: Any,
    max_steps: int = MAX_STEPS,
    fifo_max: int = FIFO_MAX_TURNS,
    fifo_min: int = FIFO_MIN_TURNS,
    verbose: bool = True,
    tool_schemas: list[dict] | None = None,
    system_prompt: str | None = None,
    user_suffix: str | None = None,
    file_state_cache: FileStateCache | None = None,
) -> AgentResult:
    if tool_schemas is None:
        tool_schemas = TOOL_SCHEMAS
    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT
    if file_state_cache is None:
        file_state_cache = FileStateCache()
    fifo_drop = fifo_max - fifo_min
    if not 0 <= fifo_min < fifo_max:
        raise ValueError("FIFO limits must satisfy 0 <= min < max")
    fifo_offset = 0
    condense_events: list[dict] = []
    _user_content = build_user_prompt(question, source_files)
    if user_suffix:
        _user_content = _user_content + "\n\n" + user_suffix
    messages: list[dict] = [{"role": "system", "content": system_prompt}, {"role": "user", "content": _user_content}]
    trace: list[TraceStep] = []
    trace.append(TraceStep(step=0, role="user", content=messages[1]["content"]))
    final_answer: str | None = None
    full_assistant_output: str | None = None
    finish_reason = "max_steps"
    error: str | None = None
    steps = 0
    recent_turn_sigs: deque[list[str]] = deque(maxlen=fifo_max)
    overflow_state = "none"
    force_final_reason: str | None = None
    reminder_fired = False
    if verbose:
        print(f"\n[agent {uid}] ▶ {question[:120]}...")
    try:
        for step in range(1, max_steps + 1):
            steps = step
            windowed, fifo_offset, _dropped = _fifo_condense(messages, fifo_offset, max_turns=fifo_max, drop=fifo_drop)
            if _dropped:
                condense_events.append({"step": step, "offset_after": fifo_offset, "dropped": _dropped})
                for _ in range(_dropped):
                    if recent_turn_sigs:
                        recent_turn_sigs.popleft()
            try:
                resp = await llm.chat(messages=windowed, tools=tool_schemas, tool_choice="auto")
            except Exception as e:
                if is_context_overflow_error(e):
                    if overflow_state == "none":
                        messages, trimmed = _trim_last_tool_pair(messages)
                        overflow_state = "trimmed_once"
                        msg = f"context overflow at step {step}, trimmed last tool pair (trimmed={trimmed!r}), retrying"
                        trace.append(TraceStep(step=step, role="system", content=f"[overflow] {msg}"))
                        if verbose:
                            print(f"  ↻ [step {step}] {msg}")
                        if trimmed:
                            if recent_turn_sigs:
                                recent_turn_sigs.pop()
                            continue
                    force_final_reason = "exceeded the LLM context budget"
                    overflow_state = "forced_final"
                    finish_reason = "context_overflow"
                    if verbose:
                        print(f"  ✖ [step {step}] context overflow, going to force-final fallback")
                    break
                error = f"LLM 调用失败 step={step}: {type(e).__name__}: {e}"
                finish_reason = "llm_error"
                trace.append(TraceStep(step=step, role="error", content=error))
                if verbose:
                    print(f"  ✖ [step {step}] {error}")
                break
            content = resp.get("content") or ""
            tool_calls = resp.get("tool_calls") or []
            usage = resp.get("usage")
            reasoning_content = resp.get("reasoning_content")
            trace.append(
                TraceStep(
                    step=step,
                    role="assistant",
                    content=content,
                    tool_calls=tool_calls,
                    usage=usage,
                    reasoning_content=reasoning_content,
                )
            )
            if verbose:
                tc_names = [t["function"]["name"] for t in tool_calls] if tool_calls else []
                snippet = (content or "").strip().replace("\n", " ")[:160]
                print(f"  [step {step}] tools={tc_names} content={snippet!r}")
            _fa = _extract_final_answer(content) if content else None
            if _fa is not None:
                final_answer = _fa
                full_assistant_output = content
                finish_reason = "final_answer"
                if verbose:
                    print(f"  ✓ [step {step}] FINAL_ANSWER={final_answer!r}")
                final_asst_msg = {"role": "assistant", "content": content or ""}
                _attach_reasoning(final_asst_msg, reasoning_content, context_offset=fifo_offset)
                messages.append(final_asst_msg)
                break
            if not tool_calls:
                _fr = resp.get("finish_reason")
                if _fr == "length":
                    force_final_reason = "been truncated by the max_tokens budget"
                    finish_reason = "length"
                    if verbose:
                        print(
                            f"  ✖ [step {step}] finish_reason=length, going to force-final fallback (single-shot, no retry)"
                        )
                    asst_msg = {"role": "assistant", "content": content or ""}
                    _attach_reasoning(asst_msg, reasoning_content, context_offset=fifo_offset)
                    messages.append(asst_msg)
                    break
                if _fr == "stop" and content:
                    asst_msg = {"role": "assistant", "content": content}
                    _attach_reasoning(asst_msg, reasoning_content, context_offset=fifo_offset)
                    messages.append(asst_msg)
                    followup_user = "You did not include <FINAL_ANSWER>...</FINAL_ANSWER>. If you have enough info, output ONLY a final answer in that tag now. Otherwise, continue investigating using tools."
                    messages.append({"role": "user", "content": followup_user})
                    trace.append(TraceStep(step=step, role="user", content=followup_user))
                    recent_turn_sigs.append([])
                    continue
                error = f"Empty assistant turn at step {step}; finish_reason={_fr}"
                finish_reason = "empty_turn"
                if verbose:
                    print(f"  ✖ [step {step}] {error}")
                break
            asst_msg = {"role": "assistant", "content": content, "tool_calls": tool_calls}
            _attach_reasoning(asst_msg, reasoning_content, context_offset=fifo_offset)
            messages.append(asst_msg)
            tool_results: list[dict] = []
            hit_repeated = False
            turn_sigs: list[str] = []
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                args_str = tc["function"]["arguments"]
                args = _parse_tool_arguments(args_str)
                tool_call_id = tc["id"]
                sig = _tool_call_signature(tool_name, args)
                if verbose:
                    args_snip = json.dumps(args, ensure_ascii=False)[:200]
                    print(f"     → tool {tool_name} args={args_snip}")
                try:
                    result_text = await dispatch_tool(
                        tool_name, args, sandbox=sandbox, file_state_cache=file_state_cache
                    )
                except Exception as e:
                    result_text = f"[tool {tool_name}] 执行异常: {type(e).__name__}: {e}"
                if verbose:
                    out_snip = (result_text or "")[:200].replace("\n", " ")
                    print(f"       ← result ({len(result_text)} chars): {out_snip!r}")
                tool_results.append({"tool_call_id": tool_call_id, "name": tool_name, "result": result_text})
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call_id, "name": tool_name, "content": result_text}
                )
                _is_unknown_tool = result_text.startswith("[dispatch_tool] 未知工具:")
                turn_sigs.append(sig)
                if _is_unknown_tool:
                    visible_sigs = list(chain.from_iterable(recent_turn_sigs)) + turn_sigs
                    recent_count = visible_sigs.count(sig)
                    if verbose:
                        print(
                            f"       [unknown tool repeat={recent_count}/{MAX_REPEATED_CALL} in last {fifo_max} turns]"
                        )
                    if recent_count >= MAX_REPEATED_CALL:
                        hit_repeated = True
                        if verbose:
                            print(
                                f"  ✖ [step {step}] unknown tool {tool_name} repeated {recent_count} times, forcing final answer"
                            )
                        break
            recent_turn_sigs.append(turn_sigs)
            trace[-1].tool_results = tool_results
            if hit_repeated:
                executed_ids = {r["tool_call_id"] for r in tool_results}
                for tc in tool_calls:
                    if tc["id"] not in executed_ids:
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "name": tc["function"]["name"],
                                "content": "[skipped: repeated call detected, stopping early]",
                            }
                        )
                force_final_reason = (
                    f"repeated the same tool call {MAX_REPEATED_CALL} times in the last {fifo_max} turns"
                )
                finish_reason = "repeated_tool"
                break
            remaining_steps = max_steps - step
            if not reminder_fired and 0 < remaining_steps <= STEP_REMINDER_THRESHOLD:
                reminder_text = f"[Reminder] You have {remaining_steps} step(s) remaining out of {max_steps}. Consolidate your findings and emit the <REASONING>...</REASONING><FINAL_ANSWER>...</FINAL_ANSWER> block before the budget is exhausted."
                messages.append({"role": "user", "content": reminder_text})
                trace.append(TraceStep(step=step, role="user", content=reminder_text))
                reminder_fired = True
                if verbose:
                    print(f"  ⏰ [step {step}] reminder injected ({remaining_steps} step(s) left, fire-once)")
        else:
            finish_reason = "max_steps"
            force_final_reason = "reached the maximum number of steps"
            if verbose:
                print(f"  ✖ 超过最大步数 {max_steps}")
    except Exception as e:
        error = f"Agent loop 异常: {type(e).__name__}: {e}"
        finish_reason = "exception"
    if final_answer is None and force_final_reason is not None:
        if verbose:
            print(f"  ▶ force-final-answer fallback ({force_final_reason})")
        ff_answer, ff_content, ff_user, ff_reasoning = await _force_final_answer(
            llm,
            messages,
            fifo_offset=fifo_offset,
            fifo_max=fifo_max,
            fifo_drop=fifo_drop,
            why=force_final_reason,
            verbose=verbose,
        )
        if ff_content is not None:
            full_assistant_output = ff_content
        if ff_answer:
            final_answer = ff_answer
            if verbose:
                print(f"  ✓ force-final-answer FINAL_ANSWER={final_answer!r}")
        elif verbose:
            print("  ✖ force-final-answer did NOT produce a FINAL_ANSWER tag")
        trace.append(TraceStep(step=steps + 1, role="user", content=ff_user))
        trace.append(TraceStep(step=steps + 2, role="assistant", content=ff_content, reasoning_content=ff_reasoning))
        messages.append({"role": "user", "content": ff_user})
        ff_asst_msg = {"role": "assistant", "content": ff_content or ""}
        _attach_reasoning(
            ff_asst_msg,
            ff_reasoning,
            context_offset=_fifo_condense(messages, fifo_offset, max_turns=fifo_max, drop=fifo_drop)[1],
        )
        messages.append(ff_asst_msg)
    main_agent_message_history = _build_main_agent_message_history(
        system_prompt=system_prompt, tool_schemas=tool_schemas, messages=messages
    )
    main_agent_message_history["fifo"] = {"max": fifo_max, "min": fifo_min, "events": condense_events}
    return AgentResult(
        uid=uid,
        question=question,
        final_answer=final_answer,
        full_assistant_output=full_assistant_output,
        steps_used=steps,
        finish_reason=finish_reason,
        error=error,
        trace=trace,
        system_prompt=system_prompt,
        tool_schemas=list(tool_schemas),
        main_agent_message_history=main_agent_message_history,
    )
