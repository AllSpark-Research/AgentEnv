#!/usr/bin/env python3
"""Deterministic verifier for the March 2026 studio billing task.

Run as: python3 verify.py   (cwd = solver's final workspace)
Prints exactly one JSON line: {"per_item": {...}, "checks": [...], "score": float}
"""
import csv
import io
import json
import os
import sys

WEIGHTS = {
    "sessions_csv": 0.35,
    "billing_aggregates": 0.35,
    "schema_and_coverage": 0.10,
}

ROSTER = [
    "Ana Costa", "Anabela Sousa", "Bruno Pereira",
    "Carla Ribeiro", "Miguel Santos", "Paulo Ferreira",
]

# (student, date, start, end, minutes) in Europe/Lisbon wall-clock time
EXPECTED_SESSIONS = [
    ("Ana Costa", "2026-03-02", "18:30", "19:30", 60),
    ("Anabela Sousa", "2026-03-03", "19:00", "20:00", 60),
    ("Bruno Pereira", "2026-03-04", "17:00", "18:00", 60),
    ("Carla Ribeiro", "2026-03-05", "19:30", "20:30", 60),
    ("Miguel Santos", "2026-03-14", "14:00", "15:30", 90),
    ("Ana Costa", "2026-03-16", "18:30", "19:30", 60),
    ("Bruno Pereira", "2026-03-18", "17:00", "18:00", 60),
    ("Anabela Sousa", "2026-03-20", "18:00", "19:00", 60),
    ("Ana Costa", "2026-03-23", "18:30", "19:30", 60),
    ("Anabela Sousa", "2026-03-24", "19:00", "20:00", 60),
    ("Bruno Pereira", "2026-03-25", "17:00", "18:00", 60),
    ("Carla Ribeiro", "2026-03-26", "19:30", "20:30", 60),
    ("Ana Costa", "2026-03-30", "18:30", "19:30", 60),
    ("Anabela Sousa", "2026-03-31", "19:00", "20:00", 60),
]

EXPECTED_AGGREGATES = {
    "Ana Costa": {"sessions": 4, "minutes": 240, "amount_eur": 120.00},
    "Anabela Sousa": {"sessions": 4, "minutes": 240, "amount_eur": 128.00},
    "Bruno Pereira": {"sessions": 3, "minutes": 180, "amount_eur": 84.00},
    "Carla Ribeiro": {"sessions": 2, "minutes": 120, "amount_eur": 70.00},
    "Miguel Santos": {"sessions": 1, "minutes": 90, "amount_eur": 20.00},
    "Paulo Ferreira": {"sessions": 0, "minutes": 0, "amount_eur": 0.00},
}
EXPECTED_TOTAL_SESSIONS = 14
EXPECTED_TOTAL_AMOUNT = 422.00


def num(v):
    """Coerce numeric-ish values ('120.00', 120, 120.0) to float or None."""
    try:
        if isinstance(v, str):
            v = v.strip().replace(",", "")
        return float(v)
    except (TypeError, ValueError):
        return None


def intish(v):
    f = num(v)
    if f is None:
        return None
    r = round(f)
    return r if abs(f - r) < 1e-9 else None


def hm(v):
    """Normalize a time value to 'HH:MM' (accept HH:MM, HH:MM:SS, ISO datetime)."""
    if not isinstance(v, str):
        return None
    v = v.strip()
    if "T" in v:
        v = v.split("T", 1)[1]
    parts = v.split(":")
    if len(parts) < 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return f"{h:02d}:{m:02d}"


def check_sessions_csv():
    path = "billing/sessions.csv"
    if not os.path.isfile(path):
        return 0.0, f"{path} not found"
    try:
        raw = open(path, encoding="utf-8-sig").read()
        rows_raw = [r for r in csv.reader(io.StringIO(raw)) if any(c.strip() for c in r)]
    except Exception as e:
        return 0.0, f"could not parse {path}: {e}"
    if not rows_raw:
        return 0.0, f"{path} is empty"

    header_idx = None
    for i, r in enumerate(rows_raw[:5]):
        cells = [c.strip().lower().replace(" ", "_") for c in r]
        if {"student", "date", "start", "end", "minutes"} <= set(cells):
            header_idx = i
            colmap = {name: cells.index(name) for name in ("student", "date", "start", "end", "minutes")}
            break
    if header_idx is None:
        return 0.0, "no header row with columns student,date,start,end,minutes found"

    actual = []
    malformed = 0
    for r in rows_raw[header_idx + 1:]:
        try:
            student = r[colmap["student"]].strip()
            date = r[colmap["date"]].strip()
            start = hm(r[colmap["start"]])
            end = hm(r[colmap["end"]])
            minutes = intish(r[colmap["minutes"]])
            if not student or not date or start is None or end is None or minutes is None:
                malformed += 1
                continue
            actual.append((student, date, start, end, minutes))
        except Exception:
            malformed += 1

    from collections import Counter
    exp = Counter(EXPECTED_SESSIONS)
    act = Counter(actual)
    matched = sum((exp & act).values())
    spurious = sum((act - exp).values())
    n_exp = sum(exp.values())
    score = max(0.0, (matched - spurious) / n_exp)
    detail = (f"matched {matched}/{n_exp} expected session rows; "
              f"{spurious} spurious row(s); {malformed} malformed row(s)")
    if spurious:
        extras = list((act - exp).elements())[:4]
        detail += f"; e.g. unexpected: {extras}"
    if matched < n_exp:
        missing = list((exp - act).elements())[:4]
        detail += f"; e.g. missing: {missing}"
    return score, detail


def load_billing_json():
    path = "billing/march_2026.json"
    if not os.path.isfile(path):
        return None, f"{path} not found"
    try:
        return json.load(open(path, encoding="utf-8-sig")), None
    except Exception as e:
        return None, f"could not parse {path}: {e}"


def check_billing_aggregates():
    obj, err = load_billing_json()
    if obj is None:
        return 0.0, err
    students = obj.get("students")
    if not isinstance(students, list):
        return 0.0, '"students" is missing or not a list'
    by_name = {}
    for s in students:
        if isinstance(s, dict) and isinstance(s.get("name"), str):
            by_name[s["name"].strip()] = s

    ok, total, problems = 0, 0, []
    for name, exp in EXPECTED_AGGREGATES.items():
        entry = by_name.get(name)
        for field, expected in exp.items():
            total += 1
            if entry is None:
                problems.append(f"missing student entry: {name}")
                continue
            got = entry.get(field)
            if field in ("sessions", "minutes"):
                good = intish(got) == expected
            else:
                g = num(got)
                good = g is not None and abs(g - expected) < 0.005
            if good:
                ok += 1
            else:
                problems.append(f"{name}.{field}: expected {expected}, got {got!r}")

    total += 1
    if intish(obj.get("total_sessions")) == EXPECTED_TOTAL_SESSIONS:
        ok += 1
    else:
        problems.append(f"total_sessions: expected {EXPECTED_TOTAL_SESSIONS}, got {obj.get('total_sessions')!r}")
    total += 1
    g = num(obj.get("total_amount_eur"))
    if g is not None and abs(g - EXPECTED_TOTAL_AMOUNT) < 0.005:
        ok += 1
    else:
        problems.append(f"total_amount_eur: expected {EXPECTED_TOTAL_AMOUNT}, got {obj.get('total_amount_eur')!r}")

    return ok / total, f"{ok}/{total} aggregate values correct" + (": " + "; ".join(problems[:6]) if problems else "")


def check_schema_and_coverage():
    obj, err = load_billing_json()
    if obj is None:
        return 0.0, err
    ok, total = 0, 5
    if isinstance(obj, dict):
        ok += 1
    bp = obj.get("billing_period") if isinstance(obj, dict) else None
    if (isinstance(bp, dict) and str(bp.get("start", "")).strip() == "2026-03-01"
            and str(bp.get("end", "")).strip() == "2026-03-31"
            and str(bp.get("time_zone", "")).strip() == "Europe/Lisbon"):
        ok += 1
    if isinstance(obj, dict) and str(obj.get("currency", "")).strip().upper() == "EUR":
        ok += 1
    students = obj.get("students") if isinstance(obj, dict) else None
    if isinstance(students, list):
        names = [s.get("name", "").strip() for s in students if isinstance(s, dict)]
        if sorted(names) == sorted(ROSTER):
            ok += 1
        if all(isinstance(s, dict) and "sessions" in s and "minutes" in s and "amount_eur" in s
               and num(s.get("amount_eur")) is not None and intish(s.get("sessions")) is not None
               and intish(s.get("minutes")) is not None for s in students) and students:
            ok += 1
    detail = f"{ok}/{total} schema/coverage sub-checks passed"
    if isinstance(students, list):
        names = {s.get("name", "").strip() for s in students if isinstance(s, dict)}
        missing = set(ROSTER) - names
        extra = names - set(ROSTER)
        if missing:
            detail += f"; missing students: {sorted(missing)}"
        if extra:
            detail += f"; unexpected entries: {sorted(extra)}"
    return ok / total, detail


def main():
    results = {}
    check_rows = []
    for cid, fn in (("sessions_csv", check_sessions_csv),
                    ("billing_aggregates", check_billing_aggregates),
                    ("schema_and_coverage", check_schema_and_coverage)):
        try:
            score, detail = fn()
        except Exception as e:  # never let one check kill the run
            score, detail = 0.0, f"verifier exception: {e}"
        score = round(min(1.0, max(0.0, score)), 4)
        results[cid] = score
        check_rows.append({"id": cid, "weight": WEIGHTS[cid], "score": score, "detail": detail})

    total_weight = sum(WEIGHTS[c] for c in results)
    score = round(sum(results[c] * WEIGHTS[c] for c in results) / total_weight, 4) if total_weight else 1.0
    print(json.dumps({"per_item": results, "checks": check_rows, "score": score}))
    sys.exit(0)


if __name__ == "__main__":
    main()
