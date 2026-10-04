#!/usr/bin/env python3
"""Deterministic verifier for the Lumen Books v2.3.0 release-prep task.

Run from the solver's final workspace root. Prints exactly one JSON line and
always exits 0.
"""
import json
import os
import re
import subprocess
import sys
from decimal import Decimal

PROD_SCHEMA = "schema/prod_2024-08-01.sql"
EXTRACT = "data/prod_extract_2024-08-01.sql"
TARGET = "schema/target_v2.3.0.sql"
MIGRATION = "migrations/V2_3_0__release.sql"
REPORT = "reports/schema_diff_report.md"
CI_GATE = "ci/check_schema_drift.sh"

WEIGHTS = {"D1": 0.30, "D2": 0.22, "D3": 0.13, "D4": 0.15}
results = {}   # rubric id -> (score, detail)


def record(rid, score, detail):
    results[rid] = (max(0.0, min(1.0, score)), detail)


# ---------------------------------------------------------------- D1/D2
def _norm_type(t):
    t = " ".join((t or "").upper().split())
    return {"INT": "INTEGER"}.get(t, t)


def _fingerprint(con):
    tables = sorted(
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    )
    cols, fks, named_idx, uniq = {}, {}, {}, {}
    for t in tables:
        info = con.execute(f"PRAGMA table_info('{t}')").fetchall()
        cols[t] = sorted(
            (c[1], _norm_type(c[2]), c[3], " ".join((c[4] or "").split()), c[5])
            for c in info
        )
        fks[t] = sorted(
            (fk[2], fk[3], fk[4]) for fk in con.execute(f"PRAGMA foreign_key_list('{t}')")
        )
        nidx, uq = set(), set()
        for _, name, unique, origin, _ in con.execute(f"PRAGMA index_list('{t}')"):
            icols = tuple(r[2] for r in con.execute(f"PRAGMA index_info('{name}')"))
            if origin == "c":
                nidx.add((name, bool(unique)))
            else:
                uq.add(icols)
        named_idx[t], uniq[t] = nidx, uq
    return {"tables": tables, "cols": cols, "fks": fks, "named_idx": named_idx, "uniq": uniq}


def _build(files, migration_text=None):
    import sqlite3

    con = sqlite3.connect(":memory:")
    for f in files:
        con.executescript(open(f, encoding="utf-8").read())
    con.execute("PRAGMA foreign_keys = OFF")  # mirror SQLite driver defaults
    if migration_text is not None:
        con.executescript(migration_text)
    return con


def _cents(v):
    return int(Decimal(repr(v)) * 100)


def check_migration():
    d1_parts, d2_parts, notes = [], [], []

    try:
        mig_text = open(MIGRATION, encoding="utf-8").read()
    except Exception as e:
        record("D1", 0.0, f"migration file missing/unreadable: {e}")
        record("D2", 0.0, "no migration to apply")
        return

    # placeholder / generated-scaffold detection (policy item 1)
    low = mig_text.lower()
    if re.search(r"\btodo\b", low) or "table_name(" in low or "varchar(255)" in low:
        notes.append("migration contains generated-scaffold placeholder content")

    try:
        pre = _build([PROD_SCHEMA, EXTRACT])
        ref = _build([TARGET])
    except Exception as e:
        record("D1", 0.0, f"could not build fixture/reference DBs: {e}")
        record("D2", 0.0, "fixture build failed")
        return

    try:
        post = _build([PROD_SCHEMA, EXTRACT], migration_text=mig_text)
        d1_parts.append(1.0)
    except Exception as e:
        record("D1", 0.0, f"migration does not apply cleanly: {e}")
        record("D2", 0.0, "migration failed to apply")
        return

    # --- schema equality vs reference built from target file ---------------
    fp_ref, fp_post = _fingerprint(ref), _fingerprint(post)

    if fp_post["tables"] == fp_ref["tables"]:
        d1_parts.append(1.0)
    else:
        missing = sorted(set(fp_ref["tables"]) - set(fp_post["tables"]))
        extra = sorted(set(fp_post["tables"]) - set(fp_ref["tables"]))
        notes.append(f"table set mismatch missing={missing} extra={extra}")
        d1_parts.append(0.0)

    col_ok = all(
        fp_post["cols"].get(t) == fp_ref["cols"].get(t)
        for t in set(fp_ref["cols"]) | set(fp_post["cols"])
    )
    d1_parts.append(1.0 if col_ok else 0.0)
    if not col_ok:
        for t in set(fp_ref["cols"]) | set(fp_post["cols"]):
            if fp_post["cols"].get(t) != fp_ref["cols"].get(t):
                notes.append(f"columns mismatch on {t}")
                break

    fk_ok = all(
        fp_post["fks"].get(t) == fp_ref["fks"].get(t)
        for t in set(fp_ref["fks"]) | set(fp_post["fks"])
    )
    d1_parts.append(1.0 if fk_ok else 0.0)
    if not fk_ok:
        oi_ref = [f for f in fp_ref["fks"].get("order_items", []) if f[0] == "books"]
        oi_post = [f for f in fp_post["fks"].get("order_items", []) if f[0] == "books"]
        if oi_ref and not oi_post:
            notes.append("missing foreign key order_items.book_id -> books(id)")

    all_named = set().union(*fp_ref["named_idx"].values()) | set().union(*fp_post["named_idx"].values())
    idx_ok = True
    for t in set(fp_ref["named_idx"]) | set(fp_post["named_idx"]):
        if fp_post["named_idx"].get(t) != fp_ref["named_idx"].get(t):
            idx_ok = False
            notes.append(f"index mismatch on {t}")
            break
    d1_parts.append(1.0 if (idx_ok and all_named) else (0.5 if idx_ok else 0.0))

    uq_ok = all(
        fp_post["uniq"].get(t) == fp_ref["uniq"].get(t)
        for t in set(fp_ref["uniq"]) | set(fp_post["uniq"])
    )
    d1_parts.append(1.0 if uq_ok else 0.0)
    if not uq_ok:
        notes.append("unique-constraint mismatch (e.g. isbn UNIQUE or wishlists UNIQUE pair)")

    d1 = sum(d1_parts) / len(d1_parts)
    record(
        "D1",
        d1,
        f"{int(round(d1 * len(d1_parts)))}/{len(d1_parts)} schema-equality subchecks pass"
        + ("; " + "; ".join(notes) if notes else ""),
    )

    # --- data integrity + conversion ---------------------------------------
    kept = ["customers", "books", "orders", "order_items"]
    count_parts = []
    for t in kept:
        try:
            a = pre.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            b = post.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            ka = {r[0] for r in pre.execute(f"SELECT id FROM {t}")}
            kb = {r[0] for r in post.execute(f"SELECT id FROM {t}")}
            count_parts.append(1.0 if (a == b and ka == kb) else 0.0)
            if a != b or ka != kb:
                notes.append(f"{t}: row count/pk changed {a}->{b}")
        except Exception as e:
            count_parts.append(0.0)
            notes.append(f"{t}: data check failed ({e})")

    conv_parts = []
    for t, old, new in [
        ("books", "list_price", "price_cents"),
        ("orders", "total", "total_cents"),
        ("order_items", "unit_price", "unit_price_cents"),
    ]:
        try:
            pre_rows = dict(pre.execute(f"SELECT id, {old} FROM {t}").fetchall())
            bad = 0
            for i, v in pre_rows.items():
                got = post.execute(f"SELECT {new} FROM {t} WHERE id=?", (i,)).fetchone()
                if got is None or int(got[0]) != _cents(v):
                    bad += 1
            conv_parts.append(1.0 if bad == 0 else max(0.0, 1.0 - bad / max(1, len(pre_rows))))
            if bad:
                notes.append(f"{t}: {bad}/{len(pre_rows)} rows with wrong cent conversion")
        except Exception as e:
            conv_parts.append(0.0)
            notes.append(f"{t}: conversion check failed ({e})")

    try:
        viol = post.execute("PRAGMA foreign_key_check").fetchall()
        fk_integrity = 1.0 if not viol else 0.0
        if viol:
            notes.append(f"{len(viol)} foreign key violations")
    except Exception:
        fk_integrity = 0.0

    try:
        new_defaults = 0.0
        n = post.execute("SELECT COUNT(*) FROM customers WHERE marketing_opt_in=0").fetchone()[0]
        m = post.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        d = post.execute("SELECT COUNT(*) FROM orders WHERE discount_cents=0").fetchone()[0]
        o = post.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if n == m and d == o:
            new_defaults = 1.0
    except Exception:
        new_defaults = 0.0

    d2 = (sum(count_parts) + sum(conv_parts)) / (len(count_parts) + len(conv_parts))
    d2 = d2 * 0.85 + fk_integrity * 0.10 + new_defaults * 0.05
    record(
        "D2",
        d2,
        f"rows preserved {sum(count_parts):.0f}/{len(count_parts)} tables, "
        f"conversion {sum(conv_parts):.2f}/{len(conv_parts)} columns, fk_check={'ok' if fk_integrity else 'FAIL'}"
        + ("; " + "; ".join(notes) if notes else ""),
    )


# ---------------------------------------------------------------- D3
def check_ci_gate():
    try:
        src = open(CI_GATE, encoding="utf-8").read()
    except Exception as e:
        record("D3", 0.0, f"ci/check_schema_drift.sh missing/unreadable: {e}")
        return
    parts, notes = [], []
    parts.append(1.0 if "check-drift" in src else 0.0)
    if "check-drift" not in src:
        notes.append("does not invoke the schema-diff check-drift command")

    for actual, expect_zero, label in [
        (TARGET, True, "no-drift case"),
        (PROD_SCHEMA, False, "drift case"),
    ]:
        try:
            p = subprocess.run(
                ["bash", CI_GATE, actual],
                capture_output=True, text=True, timeout=60, cwd=os.getcwd(),
            )
            ok = (p.returncode == 0) if expect_zero else (p.returncode != 0)
            parts.append(1.0 if ok else 0.0)
            if not ok:
                notes.append(f"{label}: exit {p.returncode} (stderr: {p.stderr.strip()[:120]})")
        except Exception as e:
            parts.append(0.0)
            notes.append(f"{label}: failed to run ({e})")
    record("D3", sum(parts) / len(parts), "; ".join(notes) if notes else "gate passes both cases")


# ---------------------------------------------------------------- D4
def check_report():
    try:
        text = open(REPORT, encoding="utf-8").read().lower()
    except Exception as e:
        record("D4", 0.0, f"report missing/unreadable: {e}")
        return

    groups = {
        "renames classified as renames": all(x in text for x in ["list_price", "price_cents", "rename"]),
        "total_cents conversion": all(x in text for x in ["total", "total_cents"]),
        "unit_price conversion": all(x in text for x in ["unit_price", "unit_price_cents"]),
        "added columns": all(x in text for x in ["marketing_opt_in", "discount_cents"]),
        "new tables": all(x in text for x in ["reviews", "wishlists"]),
        "removed tables": all(x in text for x in ["legacy_promo_codes", "temp_dba_scratchpad"]),
        "index changes": all(x in text for x in ["idx_books_isbn", "idx_books_price_perf", "idx_orders_status"]),
        "added foreign key": bool(
            re.search(r"order_items", text)
            and re.search(r"foreign key|references books|\bfk\b", text)
        ),
        "conversion risk / exactness": bool(re.search(r"round|exact|truncat|float", text)),
        "destructive-change authorization": bool(re.search(r"ops-1188|backup", text)),
    }
    score = sum(1.0 for v in groups.values() if v) / len(groups)
    missing = [k for k, v in groups.items() if not v]
    record(
        "D4",
        score,
        f"{len(groups) - len(missing)}/{len(groups)} required items covered"
        + ("; missing: " + ", ".join(missing) if missing else ""),
    )


for fn in (check_migration, check_ci_gate, check_report):
    try:
        fn()
    except Exception as e:  # a verifier bug leaves affected items at 0.0
        sys.stderr.write(f"verifier section error in {fn.__name__}: {e}\n")

for rid in WEIGHTS:
    if rid not in results:
        record(rid, 0.0, "check did not run")

total_weight = sum(WEIGHTS.values())
score = sum(results[r][0] * WEIGHTS[r] for r in WEIGHTS) / total_weight

out = {
    "per_item": {rid: round(results[rid][0], 4) for rid in WEIGHTS},
    "checks": [
        {"id": rid, "weight": WEIGHTS[rid], "score": round(results[rid][0], 4), "detail": results[rid][1]}
        for rid in WEIGHTS
    ],
    "score": round(score, 4),
}
print(json.dumps(out))
sys.exit(0)
