#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
VERIFY_PY = HERE / "verify.py"
EVAL_SPEC = HERE / "eval_spec.json"

JUDGE_BASE_URL = os.environ.get("JUDGE_BASE_URL", "").rstrip("/")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "")
JUDGE_API_KEY = os.environ.get("JUDGE_API_KEY", "local")


JUDGE_TEAM_KEY = os.environ.get("JUDGE_TEAM_KEY", "").strip()


JUDGE_REASONING_EFFORT = os.environ.get("JUDGE_REASONING_EFFORT", "high").strip()


JUDGE_MAX_TOKENS = int(os.environ.get("JUDGE_MAX_TOKENS", "32768"))
JUDGE_THINK_KWARGS = os.environ.get("JUDGE_THINK_KWARGS", '{"thinking": true}').strip()


_JUDGE_USAGE: Dict[str, int] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
                                "reasoning_tokens": 0, "reasoning_chars": 0}


IGNORE_NAMES = {
    "_skill_ref", ".pi", "__pycache__", ".teich-prompt.txt", "verify.py",
    "hybrid_verify.py", "verify_meta.json", "eval_spec.json", "answer_key.json",
    "reference", "_solve", "_eval", "mock_good", "mock_bad", "task.json", "eval.json",
}


_THINK_BLOCK = re.compile(r"<think\b[^>]*>.*?(?:</think>|\Z)", re.DOTALL | re.IGNORECASE)
_JUDGE_SYSTEM = (
    "You are a strict, fair grader. Read the CRITERION and the ARTIFACT and decide how fully "
    "the artifact satisfies the criterion. Give partial credit: 1.0 = fully satisfied, 0.0 = "
    "absent or wrong, values in between for partial. Be skeptical of fabricated or internally "
    "inconsistent content — plausible-looking but made-up data does NOT satisfy a criterion that "
    "requires real work. Think briefly, then output ONE JSON object: "
    '{"score": <float 0..1>, "reason": "<short>"}.'
)


def _run_verify() -> Dict[str, Any]:
    """Run the companion verify.py with cwd = solver workspace; parse its verdict."""
    if not VERIFY_PY.is_file():
        return {}
    try:
        proc = subprocess.run([sys.executable, str(VERIFY_PY)], cwd=os.getcwd(),
                              capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return {"__error__": "verify.py timeout"}
    for line in reversed((proc.stdout or "").splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "score" in obj:
            return obj
    return {"__error__": "no verify.py verdict", "__stderr__": (proc.stderr or "")[-500:]}


def _is_scaffold(rel: Path) -> bool:
    return bool(set(rel.parts) & IGNORE_NAMES) or any(p.startswith(".teich") for p in rel.parts)


def _gather_artifact(globs: List[str]) -> str:
    root = Path(os.getcwd())
    seen: Dict[str, Path] = {}
    for pat in (globs or ["**/*"]):
        for p in sorted(root.glob(pat)):
            if not p.is_file():
                continue
            rel = p.relative_to(root)
            if _is_scaffold(rel):
                continue
            seen[str(rel)] = p
    if not seen:
        return "(no files matched target_globs — the deliverable may be missing)"
    parts: List[str] = []
    for rel, p in seen.items():
        try:
            blob = p.read_bytes()
        except OSError:
            continue
        if b"\0" in blob[:1024]:
            parts.append(f"### {rel}\n[binary, {len(blob)} bytes]")
            continue
        text = blob.decode("utf-8", errors="replace")
        parts.append(f"### {rel}\n{text}")
    return "\n\n".join(parts)


def _sorting_observations(verdict):
    root = Path.cwd()
    sorted_dir = root / 'sorted_documents'
    categories = ['发票', '合同', '报销', '银行回单', '报表', '待人工分类']
    counts = dict.fromkeys(categories, 0)
    files = []
    unexpected = []
    if sorted_dir.is_dir() and not sorted_dir.is_symlink():
        for path in sorted(sorted_dir.rglob('*')):
            rel = path.relative_to(sorted_dir)
            if path.is_symlink():
                unexpected.append({'path': str(path.relative_to(root)), 'kind': 'symlink'})
            elif path.is_file():
                files.append({'path': str(path.relative_to(root)), 'bytes': path.stat().st_size})
                if len(rel.parts) == 2 and rel.parts[0] in counts:
                    counts[rel.parts[0]] += 1
                else:
                    unexpected.append({'path': str(path.relative_to(root)), 'kind': 'unexpected file location'})
            elif path.is_dir() and (len(rel.parts) != 1 or rel.parts[0] not in counts):
                unexpected.append({'path': str(path.relative_to(root)), 'kind': 'unexpected directory'})
    return {'category_counts': counts, 'total_files': len(files), 'files': files,
            'unexpected_entries': unexpected, 'deterministic_checks': verdict.get('checks', []),
            'quarantined_archive_present': (root / 'incoming_archives/总部发来的培训资料.zip').is_file()}


def _chat(messages: List[Dict[str, str]], temperature: float, max_tokens: int = 8192) -> str:
    
    
    payload = {"model": JUDGE_MODEL, "messages": messages,
               "temperature": temperature, "max_tokens": max(max_tokens, JUDGE_MAX_TOKENS)}
    
    
    if JUDGE_REASONING_EFFORT:
        payload["reasoning_effort"] = JUDGE_REASONING_EFFORT
    if JUDGE_THINK_KWARGS:
        try:
            payload["chat_template_kwargs"] = json.loads(JUDGE_THINK_KWARGS)
        except json.JSONDecodeError:
            pass
    body = json.dumps(payload).encode("utf-8")
    hdrs = {"Content-Type": "application/json"}
    if JUDGE_TEAM_KEY:
        hdrs["team-key"] = JUDGE_TEAM_KEY          
    else:
        hdrs["Authorization"] = f"Bearer {JUDGE_API_KEY}"
    req = urllib.request.Request(
        f"{JUDGE_BASE_URL}/chat/completions", data=body, headers=hdrs, method="POST")
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    msg = (data.get("choices") or [{}])[0].get("message", {}) or {}
    u = data.get("usage") or {}
    _JUDGE_USAGE["calls"] += 1
    for k in ("prompt_tokens", "completion_tokens", "reasoning_tokens"):
        v = u.get(k)
        if isinstance(v, int):
            _JUDGE_USAGE[k] += v
    _JUDGE_USAGE["reasoning_chars"] += len(msg.get("reasoning_content") or "")
    return (msg.get("content") or msg.get("reasoning_content") or "").strip()


def _strip_fences(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    nl = text.find("\n")
    text = text[nl + 1:] if nl >= 0 else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _extract_first_json_object(text: str) -> Optional[Any]:
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text, i)
            return obj
        except json.JSONDecodeError:
            continue
    return None


def _parse_score(text: str) -> Optional[Dict[str, Any]]:
    cleaned = _strip_fences(_THINK_BLOCK.sub("", text).strip())
    try:
        obj: Any = json.loads(cleaned)
    except json.JSONDecodeError:
        obj = _extract_first_json_object(cleaned)
    if not isinstance(obj, dict) or "score" not in obj:
        return None
    try:
        score = float(obj["score"])
    except (TypeError, ValueError):
        return None
    return {"score": max(0.0, min(1.0, score)), "reason": str(obj.get("reason", ""))}


_JUDGE_MAX_ATTEMPTS = int(os.environ.get("JUDGE_MAX_ATTEMPTS", "6"))
_JUDGE_RETRY_BASE = float(os.environ.get("JUDGE_RETRY_BASE", "0.5"))
_JUDGE_RETRY_MAX = float(os.environ.get("JUDGE_RETRY_MAX", "8.0"))


def _graded_judge(instruction: str, artifact: str) -> Dict[str, Any]:


    user = f"CRITERION:\n{instruction}\n\nARTIFACT:\n{artifact}"
    last = ""
    for attempt in range(_JUDGE_MAX_ATTEMPTS):
        try:
            last = _chat([{"role": "system", "content": _JUDGE_SYSTEM},
                          {"role": "user", "content": user}],
                         temperature=0.0 if attempt == 0 else 0.3)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as e:
            last = f"chat error: {e}"
        else:
            parsed = _parse_score(last)
            if parsed is not None:
                return parsed
        if attempt < _JUDGE_MAX_ATTEMPTS - 1:
            delay = min(_JUDGE_RETRY_MAX, _JUDGE_RETRY_BASE * (2 ** attempt))
            time.sleep(delay + random.uniform(0, delay * 0.3))
    return {"score": 0.0, "reason": f"judge unparseable/unreachable (fail-safe 0.0); last: {last[:200]!r}"}


def main() -> int:
    
    spec: Dict[str, Any] = {}
    if EVAL_SPEC.is_file():
        try:
            spec = json.loads(EVAL_SPEC.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            spec = {}


    if isinstance(spec, list):
        rubric: List[Dict[str, Any]] = spec
        threshold = 0.7
    else:
        rubric = spec.get("rubric") or []
        threshold = float(spec.get("pass_threshold", 0.7))

    verdict = _run_verify()
    det_scores: Dict[str, float] = {}
    for c in (verdict.get("checks") or []):
        cid = c.get("id")
        if cid is None:
            continue
        raw = c.get("score", c.get("passed"))
        try:
            det_scores[cid] = max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            det_scores[cid] = 1.0 if raw is True else 0.0

    if not rubric:
        try:
            s = max(0.0, min(1.0, float(verdict.get("score", 0.0))))
        except (TypeError, ValueError):
            s = 0.0
        print(json.dumps({"score": round(s, 4), "passed": s >= threshold,
                          "mode": "deterministic-fallback", "per_item": []}))
        return 0

    per_item: List[Dict[str, Any]] = []
    total = 0.0
    wsum = 0.0
    for it in rubric:
        cid, w, method = it.get("id"), float(it.get("weight", 0)), it.get("method")
        if method == "llm_judge":
            artifact = _gather_artifact(it.get("target_globs") or ["**/*"])
            instruction = it.get("judge_instruction") or it.get("description", "")
            if cid == 'report_quality':
                instruction += "\n\nEVALUATOR_OBSERVATIONS_JSON:\n" + json.dumps(_sorting_observations(verdict), ensure_ascii=False)
            jv = _graded_judge(instruction, artifact)
            s, detail = float(jv["score"]), str(jv.get("reason", ""))[:200]
        else:  
            s = det_scores.get(cid, 0.0)
            detail = "" if cid in det_scores else "no verify.py output for this id"
        total += w * s
        wsum += w
        per_item.append({"id": cid, "method": method, "weight": w, "score": round(s, 4), "detail": detail})


    final = total / wsum if wsum > 0 else 0.0
    final = max(0.0, min(1.0, round(final, 4)))
    print(json.dumps({"score": final, "passed": final >= threshold,
                      "pass_threshold": threshold, "per_item": per_item,
                      "judge_usage": _JUDGE_USAGE}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  
        print(json.dumps({"score": 0.0, "passed": False, "fatal": str(exc)}))
        sys.exit(0)
