#!/usr/bin/env python3
"""Deterministic checks for the Bitterroot Books 2024-11-14 incident task.

Ground truth measured from the shipped workspace:
  digest (logs/app, WARN+, DATA-882 excluded): too many clients=42,
    pool acquire timeout=73, payments upstream 504=60, FATAL restarts=11,
    ERROR total=175, FATAL total=11, filtered_count=186, first error 14:03:12.
  nginx access log: 97 5xx, window 14:03:58 -> 15:34:20.
  tickets.csv: 54 rows.
  deploy-history.csv: v2.14.0 13:58 deploy, v2.13.2 15:22 rollback.
Run with cwd = solver's final workspace. Prints exactly one JSON line.
"""
import json
import re
import sys

RESULTS = {"per_item": {}, "checks": []}


def add(item_id, weight, score, detail):
    score = max(0.0, min(1.0, float(score)))
    RESULTS["per_item"][item_id] = round(score, 4)
    RESULTS["checks"].append({"id": item_id, "weight": weight,
                              "score": round(score, 4), "detail": detail[:400]})


def count_score(actual, expected, hard_tol):
    """1.0 if exact, 0.5 if within hard_tol, else 0."""
    if actual is None:
        return 0.0
    if actual == expected:
        return 1.0
    if abs(actual - expected) <= hard_tol:
        return 0.5
    return 0.0


# ---------------------------------------------------------------- digest checks
def load_digest():
    with open("incident_digest.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    if not isinstance(d, dict):
        raise ValueError("digest is not a JSON object")
    return d


def check_digest_schema():
    try:
        d = load_digest()
    except Exception as e:
        add("digest_schema", 0.10, 0.0, f"incident_digest.json missing/unparseable: {e}")
        return None
    score, notes = 0.0, []
    try:
        for k in ("total_lines", "filtered_count", "severity_counts", "patterns", "time_range"):
            if k not in d:
                notes.append(f"missing key {k}")
        if not notes:
            score += 0.4
        pats = d.get("patterns") or []
        if isinstance(pats, list) and len(pats) > 0 and int(d.get("filtered_count") or 0) > 0:
            score += 0.2
        else:
            notes.append("empty patterns/filtered_count (relative --since on historical logs?)")
        tr = d.get("time_range") or {}
        start = str(tr.get("start") or "") if isinstance(tr, dict) else str(tr)
        if "2024-11-14" in start:
            score += 0.2
        else:
            notes.append(f"time_range.start does not cover 2024-11-14: {start!r}")
        blob = json.dumps(d)
        if "checkout-api" in blob and "payments" in blob:
            score += 0.2
        else:
            notes.append("digest does not cover both services (checkout-api, payments)")
    except Exception as e:
        add("digest_schema", 0.10, score, f"partial; exception: {e}")
        return d
    add("digest_schema", 0.10, score, "; ".join(notes) if notes else "schema OK")
    return d


def check_digest_patterns(d):
    if d is None:
        add("digest_patterns", 0.30, 0.0, "no digest to inspect")
        return
    pats = d.get("patterns") or []
    score, notes = 0.0, []
    try:
        def find(rx):
            r = re.compile(rx, re.I)
            hits = [p for p in pats if r.search(str(p.get("message", "")) + " " + str(p.get("normalized", "")))]
            total = sum(int(p.get("count") or 0) for p in hits)
            return (hits[0] if hits else None), total

        p_tmc, c_tmc = find(r"too many clients")
        score += 0.30 * count_score(c_tmc if p_tmc else None, 42, 4)
        notes.append(f"too-many-clients count={c_tmc} (want 42)")

        p_pool, c_pool = find(r"connection acquire timeout|acquire.*timeout.*session_store|pool=session_store")
        score += 0.25 * count_score(c_pool if p_pool else None, 73, 5)
        notes.append(f"pool-acquire-timeout count={c_pool} (want 73)")

        p_504, c_504 = find(r"upstream checkout-api.*504|checkout/confirm.*504")
        score += 0.15 * count_score(c_504 if p_504 else None, 60, 5)
        notes.append(f"payments-upstream-504 count={c_504} (want 60)")

        p_fat, c_fat = find(r"worker process exited")
        score += 0.10 * count_score(c_fat if p_fat else None, 11, 2)
        notes.append(f"fatal-worker-restart count={c_fat} (want 11)")

        sev = d.get("severity_counts") or {}
        err = int(sev.get("ERROR") or 0)
        score += 0.10 * count_score(err, 175, 9)
        notes.append(f"ERROR total={err} (want 175)")

        noise = [p for p in pats if re.search(r"slow query|DATA-882",
                 str(p.get("message", "")) + " " + str(p.get("normalized", "")), re.I)]
        if noise:
            notes.append(f"DATA-882 slow-query noise still present ({len(noise)} pattern(s))")
        else:
            score += 0.10
    except Exception as e:
        add("digest_patterns", 0.30, score, f"exception: {e}")
        return
    add("digest_patterns", 0.30, score, "; ".join(notes))


# ---------------------------------------------------------------- report fact checks
def check_report_facts():
    try:
        with open("incident_report.md", "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        add("report_facts", 0.25, 0.0, f"incident_report.md missing: {e}")
        return
    t = text
    tl = text.lower()
    score, notes = 0.0, []

    def number_hit(target, tol):
        vals = []
        for m in re.finditer(r"\b\d[\d,]*\b", t):
            try:
                vals.append(int(m.group(0).replace(",", "")))
            except ValueError:
                continue
        if target in vals:
            return 1.0
        if any(abs(v - target) <= tol for v in vals):
            return 0.5
        return 0.0

    if "2.14.0" in t:
        score += 0.15
    else:
        notes.append("triggering deploy version v2.14.0 not cited")

    if re.search(r"13:5[5-9]", t) or "14:03" in t:
        score += 0.10
    else:
        notes.append("incident start (~13:58 deploy / 14:03 first errors) not cited")

    if re.search(r"15:2\d|15:3\d", t):
        score += 0.10
    else:
        notes.append("rollback/recovery time (15:22-15:34) not cited")

    s = number_hit(97, 1)
    if s == 1.0:
        score += 0.20
    elif s == 0.5:
        score += 0.10
        notes.append("5xx count near but not exactly 97")
    else:
        notes.append("97 5xx responses not cited")

    s = number_hit(54, 4)
    if s == 1.0:
        score += 0.15
    elif s == 0.5:
        score += 0.075
        notes.append("ticket count near but not exactly 54")
    else:
        notes.append("54 support tickets not cited")

    if re.search(r"connection pool|too many clients|pool exhaustion|max_connections|pooled", tl):
        score += 0.20
    else:
        notes.append("connection-pool / too-many-clients mechanism not named")

    secs = 0
    for kw in ("summary", "impact", "timeline", "root cause", "action"):
        if re.search(r"^#{1,4}[^\n]*" + re.escape(kw), tl, re.M):
            secs += 1
    score += 0.10 * (secs / 5.0)
    if secs < 5:
        notes.append(f"template sections found: {secs}/5")

    add("report_facts", 0.25, score, "; ".join(notes) if notes else "all forced facts cited")


# ---------------------------------------------------------------- main
def main():
    d = check_digest_schema()
    check_digest_patterns(d)
    check_report_facts()
    total_w = sum(c["weight"] for c in RESULTS["checks"])
    score = sum(c["weight"] * c["score"] for c in RESULTS["checks"]) / total_w if total_w else 1.0
    RESULTS["score"] = round(score, 4)
    print(json.dumps(RESULTS))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never fail hard; always emit a result
        print(json.dumps({"per_item": RESULTS["per_item"], "checks": RESULTS["checks"],
                          "score": RESULTS["per_item"] and
                          sum(c["weight"] * c["score"] for c in RESULTS["checks"]) /
                          max(1e-9, sum(c["weight"] for c in RESULTS["checks"])) or 0.0,
                          "fatal_error": str(e)[:300]}))
        sys.exit(0)
