#!/usr/bin/env python3
"""Deterministic verifier for the INC-2781 postmortem task.

Run as `python3 verify.py` with cwd = solver's final workspace.
Implements rubric items: incident_window, failure_accounting,
signature_and_tracing, timeline. Always prints exactly one JSON line.
"""
import csv
import io
import json
import os
import re
from datetime import datetime, timezone

GT = {
    "incident_start_utc": "2025-04-18T13:52:42.034Z",
    "incident_end_utc": "2025-04-18T15:07:13.837Z",
    "recovery_utc": "2025-04-18T15:08:05.979Z",
    "total_payment_failure_events": 261,
    "distinct_failed_orders": 71,
    "distinct_failed_requests": 87,
    "gateway_502_count": 87,
    "success_rate_window_pct": 0.0,
    "t1042_request_id": "req-bcc62b71",
    "t1042_order_id": "ORD-77517",
}


def parse_ts(value):
    """Parse an ISO-8601 timestamp leniently; return datetime or None."""
    if not isinstance(value, str):
        return None
    s = value.strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def ts_equal(a, b):
    if a is None or b is None:
        return False
    return abs((a - b).total_seconds()) < 1.0  # match to the second


def load_summary():
    if not os.path.exists("analysis/summary.json"):
        return None, "analysis/summary.json missing"
    try:
        with open("analysis/summary.json") as f:
            return json.load(f), None
    except Exception as e:
        return None, f"summary.json not valid JSON: {e}"


def check_incident_window():
    detail, subs = [], []
    try:
        s, err = load_summary()
        if s is None:
            return 0.0, err
        for key, gt in [("incident_start_utc", GT["incident_start_utc"]),
                        ("incident_end_utc", GT["incident_end_utc"]),
                        ("recovery_utc", GT["recovery_utc"])]:
            val = s.get(key)
            ok = ts_equal(parse_ts(val), parse_ts(gt))
            subs.append(ok)
            detail.append(f"{key}={'OK' if ok else f'wrong({val!r} expected {gt})'}")
        return sum(subs) / len(subs), "; ".join(detail)
    except Exception as e:
        return 0.0, f"exception: {e}"


def check_failure_accounting():
    detail, subs = [], []
    try:
        s, err = load_summary()
        if s is None:
            return 0.0, err
        for key, gt in [("total_payment_failure_events", GT["total_payment_failure_events"]),
                        ("distinct_failed_orders", GT["distinct_failed_orders"]),
                        ("distinct_failed_requests", GT["distinct_failed_requests"]),
                        ("gateway_checkout_5xx_count", GT["gateway_502_count"])]:
            val = s.get(key)
            try:
                ok = int(val) == gt
            except (TypeError, ValueError):
                ok = False
            subs.append(ok)
            detail.append(f"{key}={'OK' if ok else f'wrong({val!r} expected {gt})'}")
        return sum(subs) / len(subs), "; ".join(detail)
    except Exception as e:
        return 0.0, f"exception: {e}"


def check_signature_and_tracing():
    detail, subs = [], []
    try:
        s, err = load_summary()
        if s is None:
            return 0.0, err
        sig = str(s.get("root_cause_signature", ""))
        ok = ("401" in sig) and re.search(r"payvault|paymentgateway|unauthorized|auth_token", sig, re.I)
        subs.append(bool(ok)); detail.append(f"root_cause_signature={'OK' if ok else f'weak({sig[:60]!r})'}")
        try:
            rate = float(s.get("checkout_success_rate_pct_during_window"))
            ok = abs(rate - GT["success_rate_window_pct"]) <= 0.5
        except (TypeError, ValueError):
            ok = False
        subs.append(ok); detail.append(f"window_success_rate={'OK' if ok else 'wrong'}")
        t = s.get("t1042_request") or {}
        ok = str(t.get("request_id", "")).strip() == GT["t1042_request_id"]
        subs.append(ok); detail.append(f"t1042 request_id={'OK' if ok else f'wrong({t.get('request_id')!r})'}")
        ok = str(t.get("order_id", "")).strip() == GT["t1042_order_id"]
        subs.append(ok); detail.append(f"t1042 order_id={'OK' if ok else f'wrong({t.get('order_id')!r})'}")
        stage = str(t.get("failed_stage", "")).lower().replace("-", "").replace("_", "")
        ok = "payment" in stage and ("worker" in stage or "service" not in stage)
        subs.append(ok); detail.append(f"t1042 failed_stage={'OK' if ok else f'wrong({t.get('failed_stage')!r})'}")
        return sum(subs) / len(subs), "; ".join(detail)
    except Exception as e:
        return 0.0, f"exception: {e}"


def check_timeline():
    detail, subs = [], []
    try:
        if not os.path.exists("analysis/timeline.csv"):
            return 0.0, "analysis/timeline.csv missing"
        raw = open("analysis/timeline.csv").read()
        rdr = csv.reader(io.StringIO(raw))
        rows = [r for r in rdr if any(c.strip() for c in r)]
        if not rows:
            return 0.0, "timeline.csv empty"
        ok = [c.strip().lower() for c in rows[0]] == ["timestamp", "service", "event", "details"]
        subs.append(ok); detail.append(f"header={'OK' if ok else f'wrong({rows[0]!r})'}")
        data = rows[1:]
        subs.append(len(data) >= 5); detail.append(f"rows={len(data)}(>=5 {'OK' if len(data) >= 5 else 'too few'})")
        stamps, all_parse = [], True
        for r in data:
            ts = parse_ts(r[0] if r else "")
            if ts is None:
                all_parse = False
                break
            stamps.append(ts)
        subs.append(all_parse); detail.append(f"timestamps_parseable={'OK' if all_parse else 'no'}")
        sorted_ok = all(a <= b for a, b in zip(stamps, stamps[1:])) if all_parse else False
        subs.append(sorted_ok); detail.append(f"chronological={'OK' if sorted_ok else 'no'}")
        text = raw.lower()
        for needle, label in [("dep-20250418-c", "trigger deploy"), ("dep-20250418-d", "rollback deploy"),
                              ("inc-2781", "alert id")]:
            ok = needle in text
            subs.append(ok); detail.append(f"mentions {label}={'OK' if ok else 'missing'}")
        for gt, label in [(GT["incident_start_utc"], "incident start"),
                          (GT["recovery_utc"], "recovery")]:
            g = parse_ts(gt)
            ok = any(abs((ts - g).total_seconds()) <= 90 for ts in stamps)
            subs.append(ok); detail.append(f"has {label} row={'OK' if ok else 'missing'}")
        return sum(subs) / len(subs), "; ".join(detail)
    except Exception as e:
        return 0.0, f"exception: {e}"


def main():
    items = {
        "incident_window": 0.22,
        "failure_accounting": 0.26,
        "signature_and_tracing": 0.15,
        "timeline": 0.12,
    }
    checks, per_item, total = [], {}, 0.0
    for rid, weight in items.items():
        try:
            fn = {"incident_window": check_incident_window,
                  "failure_accounting": check_failure_accounting,
                  "signature_and_tracing": check_signature_and_tracing,
                  "timeline": check_timeline}[rid]
            score, detail = fn()
        except Exception as e:  # pragma: no cover - paranoid guard
            score, detail = 0.0, f"verifier exception: {e}"
        score = max(0.0, min(1.0, float(score)))
        per_item[rid] = score
        checks.append({"id": rid, "weight": weight, "score": score, "detail": detail})
        total += weight * score
    mass = sum(items.values())
    print(json.dumps({"per_item": per_item, "checks": checks,
                      "score": round(total / mass, 4) if mass else 1.0}))


if __name__ == "__main__":
    main()
