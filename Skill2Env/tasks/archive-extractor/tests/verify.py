#!/usr/bin/env python3
"""
Deterministic evaluator for the "weekly telemetry handoff reconciliation" task.

Run as `python3 verify.py` with cwd = solver's final workspace (workspace root).

Implements rubric items D1 (CSV structure & provenance), D2 (CSV values vs ground
truth), D3 (report dashboard table consistency with ground truth).

Ground-truth constants below were derived at authoring time from the very same raw
daily CSVs that were packed into the handoff archives (see /app/_eval/gt.json,
author-only). Every check is guarded so one failure never aborts the run.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from collections import Counter
from datetime import date, datetime

# ---------------------------------------------------------------------------
# Ground truth (author-only; mirrors the raw daily CSVs inside the archives)
# ---------------------------------------------------------------------------
EXPECTED_ROWS = [
    ("PIT", "2024-06-17", 121, 1418, 98.5),
    ("PIT", "2024-06-18", 112, 1409, 97.9),
    ("PIT", "2024-06-19", 134, 1427, 99.1),
    ("PIT", "2024-06-20", 108, 1393, 96.8),
    ("PIT", "2024-06-21", 127, 1415, 98.3),
    ("PIT", "2024-06-22", 118, 1404, 97.5),
    ("PIT", "2024-06-23", 132, 1425, 99.0),
    ("CLE", "2024-06-17", 98, 1414, 98.2),
    ("CLE", "2024-06-18", 104, 1380, 95.9),
    ("CLE", "2024-06-19", 89, 1241, 86.2),
    ("CLE", "2024-06-20", 112, 1424, 98.9),
    ("CLE", "2024-06-21", 96, 1388, 96.4),
    ("CLE", "2024-06-22", 101, 1326, 92.1),
    ("CLE", "2024-06-23", 107, 1376, 95.6),
    ("STL", "2024-06-17", 88, 1402, 97.4),
    ("STL", "2024-06-18", 95, 1422, 98.8),
    ("STL", "2024-06-19", 101, 1383, 96.1),
    ("STL", "2024-06-20", 84, 1409, 97.9),
    ("STL", "2024-06-21", 92, 1416, 98.4),
    ("STL", "2024-06-22", 97, 1392, 96.7),
    ("STL", "2024-06-23", 90, 1399, 97.2),
    ("PHX", "2024-06-17", 142, 1425, 99.0),
    ("PHX", "2024-06-18", 136, 1399, 97.2),
    ("PHX", "2024-06-19", 151, 1419, 98.6),
    ("PHX", "2024-06-20", 129, 1395, 96.9),
    ("PHX", "2024-06-21", 147, 1408, 97.8),
    ("PHX", "2024-06-22", 138, 1412, 98.1),
    ("PHX", "2024-06-23", 155, 1388, 96.4),
    ("REN", "2024-06-17", 76, 1395, 96.9),
    ("REN", "2024-06-18", 83, 1406, 97.7),
    ("REN", "2024-06-19", 71, 1411, 98.0),
    ("REN", "2024-06-20", 88, 1385, 96.2),
    ("REN", "2024-06-21", 79, 1402, 97.4),
    ("REN", "2024-06-22", 74, 1415, 98.3),
    ("REN", "2024-06-23", 85, 1393, 96.8),
]

SITES = ["PIT", "CLE", "STL", "PHX", "REN"]
DATES = [f"2024-06-{d:02d}" for d in range(17, 24)]
N_EXPECTED = len(EXPECTED_ROWS)  # 35
WEEK_START, WEEK_END = date(2024, 6, 17), date(2024, 6, 23)

EXPECTED_BY_KEY = {(s, d): (sh, rt, up) for (s, d, sh, rt, up) in EXPECTED_ROWS}
PER_SITE_TOTAL = {s: sum(sh for (ss, _d, sh, _r, _u) in EXPECTED_ROWS if ss == s) for s in SITES}
GRAND_TOTAL = sum(PER_SITE_TOTAL.values())          # 3760
AVG_UPTIME = {"PIT": 98.2, "CLE": 94.8, "STL": 97.5, "PHX": 97.7, "REN": 97.3}
EXPECTED_FLAGS = {s: ("FLAG" if AVG_UPTIME[s] < 95.0 else "OK") for s in SITES}  # CLE FLAG only

FORBIDDEN_SOURCE_TOKENS = ["backup", "snapshot", "superseded", "ren_export",
                           "deprecated", "pre-migration"]

REQUIRED_HEADER = ["site", "date", "shipments", "runtime_min", "uptime_pct", "source_archive"]

CSV_PATH = "out/handoff_consolidated.csv"
REPORT_PATH = "out/weekly_service_report.md"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def parse_date_cell(v: str):
    try:
        return datetime.strptime(v.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def parse_int(v):
    try:
        return int(str(v).strip().replace(",", "").replace(" ", ""))
    except Exception:
        return None


def parse_float(v):
    try:
        return float(str(v).strip().replace(",", ""))
    except Exception:
        return None


def read_csv_rows(path):
    """Returns (header, rows) or (None, None) on any failure."""
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            rows = list(reader)
        return header, rows
    except Exception:
        return None, None


def parse_markdown_tables(text):
    """Extract (header->index) tables from markdown pipe tables. Returns list of
    tables, each as dict {colname: [cell, ...]} over data rows."""
    tables = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < len(lines):
            header_cells = [c.strip() for c in line.strip("|").split("|")]
            j = i + 1
            if j < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[j].strip()):
                j += 1
                table = {}
                for h in header_cells:
                    table[h] = []
                while j < len(lines) and lines[j].strip().startswith("|"):
                    cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                    for idx, h in enumerate(header_cells):
                        if idx < len(cells):
                            table[h].append(cells[idx])
                    j += 1
                if any(table[h] for h in header_cells):
                    tables.append(table)
                i = j
                continue
        i += 1
    return tables


# ---------------------------------------------------------------------------
# D1 - CSV structure & provenance
# ---------------------------------------------------------------------------

def check_csv_structure():
    header, rows = read_csv_rows(CSV_PATH)
    if header is None:
        return 0.0, "consolidated CSV missing or unparseable"
    detail = []

    # header must contain all required column names (order-insensitive)
    header_norm = [h.strip().lower().replace(" ", "_") for h in header]
    header_ok = all(req in header_norm for req in REQUIRED_HEADER)
    if not header_ok:
        return 0.0, "CSV header missing required columns: " + ",".join(REQUIRED_HEADER)

    by_lower = {h.strip().lower().replace(" ", "_"): h for h in header}

    def col(name):
        return by_lower.get(name)

    score = 0.0
    # row count: exactly 35
    n = len(rows)
    if n == N_EXPECTED:
        score += 0.35
    elif n == 0:
        score += 0.0
    else:
        score += 0.35 * (min(n, N_EXPECTED) / N_EXPECTED)
        detail.append(f"row count {n} != 35")

    # dates valid & within the week
    bad_dates = 0
    for r in rows:
        d = parse_date_cell(r.get(col("date"), ""))
        if d is None or not (WEEK_START <= d <= WEEK_END):
            bad_dates += 1
    date_ok = 1.0 if bad_dates == 0 else max(0.0, 1.0 - bad_dates / max(len(rows), 1))
    score += 0.2 * date_ok
    if bad_dates:
        detail.append(f"{bad_dates} row(s) with out-of-week/invalid dates")

    # provenance: no forbidden tokens, non-empty
    forbidden_hits = 0
    empty_src = 0
    for r in rows:
        src = (r.get(col("source_archive")) or "").strip().lower()
        if not src:
            empty_src += 1
        elif any(tok in src for tok in FORBIDDEN_SOURCE_TOKENS):
            forbidden_hits += 1
    src_ok = 1.0
    if forbidden_hits or empty_src:
        src_ok = max(0.0, 1.0 - (forbidden_hits + empty_src) / max(len(rows), 1))
    score += 0.2 * src_ok
    if forbidden_hits:
        detail.append(f"{forbidden_hits} row(s) still labelled from stale/deprecated archives")

    # PHX rows must be attributed to the Phoenix artifact
    phx_rows = [r for r in rows if (r.get(col("site")) or "").strip().upper() == "PHX"]
    if phx_rows:
        phx_ok_rows = sum(1 for r in phx_rows
                          if "phx" in (r.get(col("source_archive")) or "").lower())
        phx_ok = phx_ok_rows / len(phx_rows)
    else:
        phx_ok = 0.0
    score += 0.25 * phx_ok
    if phx_rows and phx_ok < 1.0:
        detail.append("some PHX rows lack 'phx' provenance attribution")

    detail.insert(0, f"header ok; rows={n}")
    return round(min(score, 1.0), 6), "; ".join(detail[:3])


# ---------------------------------------------------------------------------
# D2 - CSV values vs ground truth
# ---------------------------------------------------------------------------

def check_csv_values():
    header, rows = read_csv_rows(CSV_PATH)
    if header is None:
        return 0.0, "consolidated CSV missing or unparseable"
    by_lower = {h.strip().lower().replace(" ", "_"): h for h in header}
    col = lambda name: by_lower.get(name)

    counts = Counter()
    parsed = []
    for r in rows:
        site = (r.get(col("site")) or "").strip().upper()
        d = parse_date_cell(r.get(col("date"), ""))
        sh = parse_int(r.get(col("shipments")))
        rt = parse_int(r.get(col("runtime_min")))
        up = parse_float(r.get(col("uptime_pct")))
        key = (site, d.isoformat() if d else None)
        counts[key] += 1
        parsed.append((key, sh, rt, up))

    matched = 0
    seen_keys = set()
    for key, sh, rt, up in parsed:
        if key in seen_keys:
            continue  # duplicate (site,date) -> invalid
        seen_keys.add(key)
        exp = EXPECTED_BY_KEY.get(key)
        if exp is None:
            continue
        e_sh, e_rt, e_up = exp
        if (sh == e_sh and rt == e_rt and up is not None
                and abs(up - e_up) <= 0.051):
            matched += 1

    score = matched / N_EXPECTED
    detail = f"{matched}/{N_EXPECTED} rows exactly match the authoritative raw data"
    return round(min(score, 1.0), 6), detail


# ---------------------------------------------------------------------------
# D3 - report dashboard table
# ---------------------------------------------------------------------------

def _norm_col(h):
    s = h.strip().lower()
    if "shipment" in s:
        return "shipments"
    if "uptime" in s:
        return "uptime"
    if "flag" in s or "status" in s:
        return "flag"
    if "received" in s:
        return "received"
    if "expected" in s:
        return "expected"
    if s in ("site", "warehouse", "location"):
        return "site"
    return s


def _find_dashboard_table(tables):
    best = None
    for t in tables:
        norm = {_norm_col(h): i for i, h in enumerate(t)}
        if "site" in norm and "shipments" in norm and "flag" in norm:
            if best is None or len(t[list(t.keys())[0]]) > len(best[list(best.keys())[0]]):
                best = t
    return best


def check_report_table():
    try:
        text = open(REPORT_PATH, "r", encoding="utf-8-sig").read()
    except Exception:
        return 0.0, "report missing or unreadable"

    tables = parse_markdown_tables(text)
    table = _find_dashboard_table(tables)
    if table is None:
        return 0.0, "no dashboard table (columns site/shipments/flag) found in report"

    norm = {_norm_col(h): h for h in table}
    col = lambda name: norm.get(name)
    if col("site") is None:
        return 0.0, "dashboard table lacks a site column"

    rows = []
    for idx, site_cell in enumerate(table[col("site")]):
        site = site_cell.strip().upper()
        r = {"site": site}
        if col("shipments"):
            r["shipments"] = parse_int(table[col("shipments")][idx])
        if col("uptime"):
            r["uptime"] = parse_float(table[col("uptime")][idx])
        if col("flag"):
            r["flag"] = (table[col("flag")][idx] or "").strip().lower()
        if col("received"):
            r["received"] = parse_int((table[col("received")][idx] or "").split("/")[0])
        if col("expected"):
            r["expected"] = parse_int((table[col("expected")][idx] or "").split("/")[0])
        rows.append(r)

    score = 0.0
    details = []
    # per-site numeric & flag checks
    site_hits = 0
    flag_hits = 0
    day_hits = 0
    for site in SITES:
        match = [r for r in rows if r["site"] == site]
        if not match:
            details.append(f"no dashboard row for {site}")
            continue
        r = match[0]
        ok_ship = r.get("shipments") == PER_SITE_TOTAL[site]
        ok_up = True
        if r.get("uptime") is not None:
            ok_up = abs(r["uptime"] - AVG_UPTIME[site]) <= 0.21
        if ok_ship and ok_up:
            site_hits += 1
        else:
            details.append(f"{site}: shipments={r.get('shipments')} (want {PER_SITE_TOTAL[site]}), "
                           f"avg_uptime={r.get('uptime')} (want {AVG_UPTIME[site]})")
        ok_flag = r.get("flag") in ("ok", "pass", "passes", "meets", "yes")
        if EXPECTED_FLAGS[site] == "FLAG":
            ok_flag = r.get("flag") in ("flag", "flagged", "fail", "breach", "below", "no", "under")
        if ok_flag:
            flag_hits += 1
        else:
            details.append(f"{site}: sla_flag='{r.get('flag')}' (want {EXPECTED_FLAGS[site]})")
        if r.get("received") == 7 and r.get("expected", 7) in (7, None):
            day_hits += 1
    score += 0.5 * (site_hits / len(SITES))       # weekly shipment + avg uptime correctness
    score += 0.3 * (flag_hits / len(SITES))       # SLA flag correctness (CLE=FLAG, others OK)

    # TOTAL row
    total_found = None
    for r in rows:
        if r["site"] in ("TOTAL", "SUM", "ALL", "ALL SITES"):
            total_found = r
            break
    if total_found is not None and total_found.get("shipments") == GRAND_TOTAL:
        score += 0.2
    elif total_found is not None:
        details.append(f"TOTAL row shipments={total_found.get('shipments')} (want {GRAND_TOTAL})")
    else:
        details.append("missing TOTAL row in dashboard table")

    detail = (f"dashboard table: {site_hits}/5 site totals ok, {flag_hits}/5 flags ok, "
              f"TOTAL ok={total_found is not None and total_found.get('shipments') == GRAND_TOTAL}; "
              + "; ".join(details[:3]))
    return round(min(score, 1.0), 6), detail


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    results = {
        "D1_csv_structure": check_csv_structure(),
        "D2_csv_values": check_csv_values(),
        "D3_report_table": check_report_table(),
    }

    weights = {"D1_csv_structure": 0.30, "D2_csv_values": 0.30, "D3_report_table": 0.15}
    det_weight = sum(weights.values())

    checks = []
    per_item = {}
    for cid, (score, detail) in results.items():
        per_item[cid] = score
        checks.append({"id": cid, "weight": weights[cid], "score": score, "detail": detail})

    score = sum(w * results[cid][0] for cid, w in weights.items()) / det_weight

    out = {"per_item": per_item, "checks": checks, "score": round(score, 6)}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())