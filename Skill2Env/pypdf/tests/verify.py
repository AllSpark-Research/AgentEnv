#!/usr/bin/env python3
"""Deterministic verifier for the Crowe & Pelley audit-packet task.

Run from the solver's final workspace root:
    python3 verify.py
Prints exactly one JSON line with per_item scores (0..1).
"""
import csv
import io
import json
import re
import sys

EXPECTED_PACKET = "packet/audit_packet.pdf"
EXPECTED_CSV = "packet/packet_index.csv"
EXPECTED_MEMO = "packet/cover_memo.md"

PAGE_MARKERS = [
    ["GL-2204", "IN WITNESS WHEREOF", "Okafor"],                # Tab A: signature page
    ["SCHEDULE 1", "FEE SCHEDULE", "18,500"],                    # Tab A: Schedule 1
    ["DECLARATIONS", "AGF-88231", "34,200"],                     # Tab B: Declarations
    ["SECTION III", "EXCLUSIONS"],                               # Tab B: Exclusions
    ["BANK RECONCILIATION", "181,410.55"],                       # Tab C: summary
    ["OUTSTANDING CHECKS", "CHK-1042"],                          # Tab C: checks detail
    ["ENGAGEMENT LETTER", "VAUGHN & HOLT", "September 27, 2024"],  # Tab D p1
    ["SCOPE OF SERVICES", "FEES AND BILLING"],                   # Tab D p2
    ["IN WITNESS WHEREOF", "P. Vaughn"],                         # Tab D p3
    ["APPENDIX A", "BILLING RATES", "425.00"],                   # Tab D p4 (Appendix A)
]
EXPECTED_PAGE_COUNT = len(PAGE_MARKERS)  # 10

ABSENT_MARKERS = [
    "GL-2240", "Northgate", "NOT EXECUTED", "FOR REVIEW ONLY",
    "AMENDMENT NO. 1", "SCHEDULE 2 -- SERVICE LEVEL",
    "SCHEDULE OF DEPOSITS IN TRANSIT", "INTERNAL SIGN-OFF",
    "CAPABILITY STATEMENT", "TABLE OF CONTENTS",
]

EXPECTED_HEADER = ["tab", "source_file", "source_pages", "packet_page_range", "page_count"]
EXPECTED_ROWS = {
    "A": ["A", "AGMT-GL-2204.pdf", "6;4", "1-2", "2"],
    "B": ["B", "AGF-88231_policy.pdf", "2;5", "3-4", "2"],
    "C": ["C", "Q3-2024_operating_reconciliation.pdf", "1;3", "5-6", "2"],
    "D": ["D", "VH_engagement_letter_v2.pdf", "1;2;3;4", "7-10", "4"],
    "TOTAL": ["TOTAL", "", "", "", "10"],
}


def load_packet():
    from pypdf import PdfReader  # guarded import
    return PdfReader(EXPECTED_PACKET)


def check_d1_packet_pages():
    try:
        reader = load_packet()
    except Exception as exc:
        return 0.0, f"cannot open {EXPECTED_PACKET}: {exc}"
    pages = reader.pages
    details = []
    count_ok = len(pages) == EXPECTED_PAGE_COUNT
    details.append(f"page_count={len(pages)} expected={EXPECTED_PAGE_COUNT}")
    page_hits = []
    for idx, markers in enumerate(PAGE_MARKERS):
        if idx >= len(pages):
            page_hits.append(0.0)
            continue
        try:
            text = pages[idx].extract_text() or ""
        except Exception:
            page_hits.append(0.0)
            continue
        missing = [m for m in markers if m not in text]
        page_hits.append(0.0 if missing else 1.0)
        if missing:
            details.append(f"p{idx}(1-based {idx+1}) missing {missing}")
    score = 0.2 * (1.0 if count_ok else 0.0) + 0.8 * (sum(page_hits) / EXPECTED_PAGE_COUNT)
    return score, "; ".join(details)[:300] or "all pages match"


def check_d2_orientation_integrity():
    try:
        reader = load_packet()
    except Exception as exc:
        return 0.0, f"cannot open {EXPECTED_PACKET}: {exc}"
    pages = reader.pages
    rot_bad = []
    for i, page in enumerate(pages):
        try:
            rot = page.rotation or 0
        except Exception:
            rot = 0
        if rot % 360 != 0:
            rot_bad.append(i + 1)
    rot_ok = 1.0 if not rot_bad else 0.0
    try:
        full = "\n".join((p.extract_text() or "") for p in pages)
    except Exception:
        full = ""
    present = [m for m in ABSENT_MARKERS if m in full]
    absent_frac = 1.0 - (len(present) / len(ABSENT_MARKERS))
    score = 0.5 * rot_ok + 0.5 * absent_frac
    detail = f"rotated_pages={rot_bad or 'none'}; forbidden_content={present or 'none'}"
    return score, detail


def check_d3_index_csv():
    try:
        with open(EXPECTED_CSV, newline="", encoding="utf-8") as f:
            rows = [[cell.strip() for cell in r] for r in csv.reader(f)]
    except Exception as exc:
        return 0.0, f"cannot read {EXPECTED_CSV}: {exc}"
    rows = [r for r in rows if any(c != "" for c in r)]
    if not rows:
        return 0.0, "csv is empty"
    header = rows[0]
    data = rows[1:]
    details = []
    header_ok = header == EXPECTED_HEADER
    if not header_ok:
        details.append(f"header={header}")
    seen = [r[0] if r else "" for r in data]
    order_ok = seen == ["A", "B", "C", "D", "TOTAL"]
    if not order_ok:
        details.append(f"row_order={seen}")
    row_scores = {}
    for row in data:
        key = row[0] if row else ""
        if key in EXPECTED_ROWS and key not in row_scores:
            norm = (row + [""] * 5)[:5]
            row_scores[key] = 1.0 if norm == EXPECTED_ROWS[key] else 0.0
            if row_scores[key] == 0.0:
                details.append(f"row {key}: got {norm}")
    correct_rows = sum(row_scores.values())
    # 20% header, 60% the four tab rows, 20% the TOTAL row
    score = 0.2 * (1.0 if header_ok else 0.0)
    score += 0.15 * sum(row_scores.get(t, 0.0) for t in ("A", "B", "C", "D"))
    score += 0.2 * row_scores.get("TOTAL", 0.0)
    if not order_ok:
        score *= 0.5
    return min(score, 1.0), "; ".join(details)[:300] or "csv exact"


def check_d4_memo_facts():
    try:
        text = open(EXPECTED_MEMO, encoding="utf-8").read()
    except Exception as exc:
        return 0.0, f"cannot read {EXPECTED_MEMO}: {exc}"
    facts = {
        "matter_number": "HLG-2024-118" in text,
        "adjusted_bank_balance": "181,410.55" in text,
        "contract_ref": "GL-2204" in text,
        "policy_ref": "AGF-88231" in text,
        "law_firm": "Vaughn" in text,
        "total_pages_10": any(
            "page" in line.lower() and re.search(r"\b10\b", line)
            for line in text.splitlines()
        ),
    }
    missing = [k for k, v in facts.items() if not v]
    return (len(facts) - len(missing)) / len(facts), f"missing_facts={missing or 'none'}"


CHECKS = {
    "D1_packet_pages": (0.30, check_d1_packet_pages),
    "D2_orientation_integrity": (0.10, check_d2_orientation_integrity),
    "D3_index_csv": (0.30, check_d3_index_csv),
    "D4_memo_facts": (0.10, check_d4_memo_facts),
}


def main():
    per_item = {}
    checks = []
    total_w = 0.0
    acc = 0.0
    for cid, (w, fn) in CHECKS.items():
        try:
            score, detail = fn()
        except Exception as exc:  # never crash the verifier
            score, detail = 0.0, f"check crashed: {exc}"
        score = max(0.0, min(1.0, float(score)))
        per_item[cid] = score
        checks.append({"id": cid, "weight": w, "score": score, "detail": detail})
        total_w += w
        acc += w * score
    final = acc / total_w if total_w else 1.0
    print(json.dumps({"per_item": per_item, "checks": checks, "score": final}))
    sys.exit(0)


if __name__ == "__main__":
    main()
