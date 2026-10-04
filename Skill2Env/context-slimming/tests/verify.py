#!/usr/bin/env python3
"""Deterministic checks for the context-slimming task.

Run as `python3 verify.py` with cwd = solver's final workspace (contains agent_workspace/).
Prints exactly one JSON line and always exits 0.
"""
import json
import os
import re
import subprocess

WS = os.path.abspath(".")
REPO = os.path.join(WS, "agent_workspace")

TOTAL_CAP = 6000
FILE_CAP = 1500
FILE_MIN = 100
CORE_FILES = ["AGENTS.md", "SOUL.md", "USER.md", "MEMORY.md", "TOOLS.md", "HEARTBEAT.md"]
DELETED_FILES = ["BOOTSTRAP.md", "IDENTITY.md"]
PRESERVE_TOKENS = ["夜航星", "NC-7", "~/.config/pearl/api_token.enc",
                   "02:00-04:00", "skill-vetter", "memory-heat-system", "prod-*"]
MOVE_MARKERS = ["user_skill_install_audit.sh", "2024-11-03"]

ITEM_WEIGHTS = {"D-structure": 0.24, "D-facts": 0.14, "D-ondemand": 0.12, "D-git": 0.10}


def top_level_md_files():
    try:
        return sorted(f for f in os.listdir(REPO)
                      if f.endswith(".md") and os.path.isfile(os.path.join(REPO, f)))
    except Exception:
        return []


def top_text():
    parts = []
    for f in top_level_md_files():
        try:
            parts.append(open(os.path.join(REPO, f), encoding="utf-8", errors="replace").read())
        except Exception:
            pass
    return "\n".join(parts)


def non_top_files():
    out = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if os.path.dirname(os.path.join(root, f)) == REPO:
                continue
            out.append(os.path.join(root, f))
    return out


def check_structure():
    try:
        files = top_level_md_files()
        checks = []  # (ok, msg)
        for f in CORE_FILES:
            ok = f in files
            checks.append((ok, f"core file {f} present" if ok else f"core file {f} MISSING"))
        for f in CORE_FILES:
            p = os.path.join(REPO, f)
            if os.path.isfile(p):
                n = os.path.getsize(p)
                ok = FILE_MIN <= n <= FILE_CAP
                checks.append((ok, f"{f} size {n}B" + (" (OK)" if ok else f" (!= {FILE_MIN}-{FILE_CAP}B)")))
        for f in DELETED_FILES:
            ok = not os.path.exists(os.path.join(REPO, f))
            checks.append((ok, f"{f} deleted" if ok else f"{f} STILL EXISTS"))
        total = sum(os.path.getsize(os.path.join(REPO, f)) for f in files)
        checks.append((total <= TOTAL_CAP, f"total injected {total}B vs cap {TOTAL_CAP}B"))
        score = sum(1 for ok, _ in checks if ok) / len(checks) if checks else 0.0
        fails = [m for ok, m in checks if not ok]
        detail = "; ".join(fails) if fails else f"7-file budget met, total {total}B"
        return score, detail
    except Exception as e:
        return 0.0, f"structure check error: {e}"


def check_facts():
    try:
        blob = top_text()
        found = [t for t in PRESERVE_TOKENS if t in blob]
        missing = [t for t in PRESERVE_TOKENS if t not in blob]
        score = len(found) / len(PRESERVE_TOKENS)
        detail = ("all tokens preserved" if not missing
                  else "missing from injected set: " + ", ".join(missing))
        return score, detail
    except Exception as e:
        return 0.0, f"facts check error: {e}"


def check_ondemand():
    try:
        top = top_text()
        agents = ""
        p_agents = os.path.join(REPO, "AGENTS.md")
        if os.path.isfile(p_agents):
            agents = open(p_agents, encoding="utf-8", errors="replace").read()
        non_top_blob = ""
        for p in non_top_files():
            try:
                non_top_blob += open(p, encoding="utf-8", errors="replace").read() + "\n"
            except Exception:
                pass
        checks = [
            ("user_skill_install_audit.sh" not in top, "audit script name still in a top-level (injected) file"),
            ("2024-11-03" not in top, "2024 archive entry still in a top-level (injected) file"),
            ("user_skill_install_audit.sh" in non_top_blob, "audit procedure NOT found in any non-top-level file"),
            ("2024-11-03" in non_top_blob, "2024 archive NOT found in any non-top-level file"),
            (bool(re.search(r"(rules|scripts|reference)/", agents)), "AGENTS.md lacks on-demand pointer (rules/|scripts/|reference/)"),
        ]
        score = sum(1 for ok, _ in checks if ok) / len(checks)
        fails = [m for ok, m in checks if not ok]
        return score, ("; ".join(fails) if fails else "detail relocated with pointers")
    except Exception as e:
        return 0.0, f"on-demand check error: {e}"


def check_git():
    try:
        def g(*args):
            return subprocess.run(["git", "-C", REPO] + list(args),
                                  capture_output=True, text=True, timeout=30)
        r = g("rev-list", "--count", "HEAD")
        if r.returncode != 0:
            return 0.0, f"not a usable git repo: {r.stderr.strip()[:120]}"
        n = int((r.stdout or "0").strip() or 0)
        head_msg = g("log", "-1", "--pretty=%B").stdout.strip()
        dirty = g("status", "--porcelain").stdout.strip()
        s = 0.0
        notes = []
        if n >= 2:
            s += 0.5
            notes.append(f"{n} commits")
        else:
            notes.append("no new commit")
        if re.search(r"瘦|slim|context|上下文|注入", head_msg, re.I):
            s += 0.25
        else:
            notes.append(f"head message lacks slimming keyword: {head_msg[:40]!r}")
        if not dirty:
            s += 0.25
        else:
            notes.append(f"dirty tree ({len(dirty.splitlines())} paths)")
        return s, "; ".join(notes)
    except Exception as e:
        return 0.0, f"git check error: {e}"


def main():
    checks = []
    per_item = {}
    for item_id, fn in [("D-structure", check_structure), ("D-facts", check_facts),
                        ("D-ondemand", check_ondemand), ("D-git", check_git)]:
        try:
            score, detail = fn()
        except Exception as e:
            score, detail = 0.0, f"unexpected error: {e}"
        per_item[item_id] = round(score, 4)
        checks.append({"id": item_id, "weight": ITEM_WEIGHTS[item_id],
                       "score": round(score, 4), "detail": detail[:300]})
    wsum = sum(ITEM_WEIGHTS.values())
    total = sum(ITEM_WEIGHTS[c["id"]] * c["score"] for c in checks) / wsum if wsum else 0.0
    print(json.dumps({"per_item": per_item, "checks": checks, "score": round(total, 4)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
