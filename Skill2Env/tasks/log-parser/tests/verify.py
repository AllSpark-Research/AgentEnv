#!/usr/bin/env python3
"""Deterministic verifier for the Luminabasket incident-triage task.

Run from the solver's final workspace root:
    python3 verify.py

Ground truth is RECOMPUTED from ./logs/*.log at runtime (the log files are
part of the initial workspace and must remain unmodified). Embedded constants
serve as a fallback if recomputation is impossible.
"""
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta

FINDINGS_PATH = "report/findings.json"
WEB_LOG = "logs/web-access.log"
AUTH_LOG = "logs/bastion-auth.log"
APP_LOG = "logs/api-service.log"

FALLBACK = {
    "incident_date_utc": "2024-11-18",
    "primary_suspicious_ip": "185.220.101.47",
    "window_start_utc": "2024-11-18T13:07:33Z",
    "window_end_utc": "2024-11-18T15:14:52Z",
    "primary_ip_request_count": 341,
    "failed_login_attempts": 380,
    "successful_logins_from_attackers": 4,
    "attack_source_ip_count": 4,
    "web_5xx_count": 169,
    "ssh_failed_password_lines": 104,
    "ssh_distinct_source_ips": 3,
    "ssh_failed_from_primary_ip": 52,
    "app_error_entries": 41,
    "compromised_accounts": ["m.hansen", "priya.k"],
}

NGINX_RE = re.compile(
    r'(?P<ip>[\d.]+) - - \[(?P<d>[^\]]+)\] "(?P<m>\w+) (?P<p>\S+) [^"]+" '
    r'(?P<s>\d+) (?P<z>\d+)'
)


def recompute_ground_truth():
    """Independently derive every expected value from the workspace logs."""
    gt = dict(FALLBACK)
    try:
        web_lines = open(WEB_LOG, encoding="utf-8", errors="ignore").read().splitlines()
    except OSError:
        return gt
    recs = []
    for line in web_lines:
        m = NGINX_RE.match(line)
        if m:
            recs.append(m.groupdict())
    if not recs:
        return gt

    # Identify the attack: non-internal IPs sending POST /api/login that got 401.
    login_401 = Counter(
        r["ip"] for r in recs
        if r["m"] == "POST" and r["p"] == "/api/login" and r["s"] == "401"
    )
    attack_ips = {ip for ip in login_401 if not ip.startswith("10.20.")}
    if not attack_ips:
        return gt
    primary = max(attack_ips, key=lambda ip: login_401[ip])
    gt["primary_suspicious_ip"] = primary
    gt["attack_source_ip_count"] = len(login_401)
    gt["failed_login_attempts"] = sum(login_401.values())
    gt["primary_ip_request_count"] = sum(1 for r in recs if r["ip"] == primary)
    gt["web_5xx_count"] = sum(1 for r in recs if int(r["s"]) >= 500)

    ok = [r for r in recs if r["p"].startswith("/api/login") and r["s"] == "200"
          and r["ip"] in attack_ips]
    gt["successful_logins_from_attackers"] = len(ok)
    accts = set()
    for r in ok:
        m = re.search(r"username=([^&\s]+)", r["p"])
        if m:
            accts.add(m.group(1))
    if accts:
        gt["compromised_accounts"] = sorted(accts)

    # Attack window: first/last request from the primary IP, converted to UTC.
    dts = []
    for r in recs:
        if r["ip"] == primary:
            try:
                dts.append(datetime.strptime(r["d"], "%d/%b/%Y:%H:%M:%S %z"))
            except ValueError:
                pass
    if dts:
        first = min(dts).astimezone(timezone.utc)
        last = max(dts).astimezone(timezone.utc)
        gt["window_start_utc"] = first.strftime("%Y-%m-%dT%H:%M:%SZ")
        gt["window_end_utc"] = last.strftime("%Y-%m-%dT%H:%M:%SZ")
        gt["incident_date_utc"] = first.strftime("%Y-%m-%d")

    try:
        auth_lines = open(AUTH_LOG, encoding="utf-8", errors="ignore").read().splitlines()
        fp = [l for l in auth_lines if "Failed password" in l]
        srcs = Counter()
        for l in fp:
            m = re.search(r"from ([\d.]+) port", l)
            if m:
                srcs[m.group(1)] += 1
        gt["ssh_failed_password_lines"] = len(fp)
        gt["ssh_distinct_source_ips"] = len(srcs)
        gt["ssh_failed_from_primary_ip"] = srcs.get(primary, 0)
    except OSError:
        pass

    try:
        app_lines = open(APP_LOG, encoding="utf-8", errors="ignore").read().splitlines()
        n_err = 0
        for l in app_lines:
            try:
                if json.loads(l).get("level") == "ERROR":
                    n_err += 1
            except (ValueError, AttributeError):
                continue
        gt["app_error_entries"] = n_err
    except OSError:
        pass
    return gt


def parse_instant(value):
    """Parse an ISO-8601-ish timestamp to an aware UTC datetime, or None."""
    if not isinstance(value, str):
        return None
    s = value.strip()
    try:
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s[:-1] + "+00:00")
        else:
            dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)  # undecorated assumed UTC
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def norm_int(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str):
        s = v.strip().replace(",", "")
        if re.fullmatch(r"-?\d+", s):
            return int(s)
    return None


def norm_str(v):
    return v.strip() if isinstance(v, str) else None


def check_r1(f, gt):
    """Attribution & correlation."""
    detail = []
    score = 0.0

    pip = norm_str(f.get("primary_suspicious_ip"))
    if pip == gt["primary_suspicious_ip"]:
        score += 0.40
    else:
        detail.append(f"primary_suspicious_ip={pip!r} (expected {gt['primary_suspicious_ip']})")

    at = (norm_str(f.get("attack_type")) or "").lower().replace("-", "_").replace(" ", "_")
    if any(k in at for k in ("credential", "stuffing", "brute", "password_guess")):
        score += 0.15
    else:
        detail.append(f"attack_type={f.get('attack_type')!r} (expected credential_stuffing-like)")

    if f.get("same_source_ip_in_web_and_ssh") is True:
        score += 0.20
    else:
        detail.append(f"same_source_ip_in_web_and_ssh={f.get('same_source_ip_in_web_and_ssh')!r} (expected true)")

    want = {a.lower() for a in gt["compromised_accounts"]}
    got_raw = f.get("compromised_accounts")
    got = set()
    if isinstance(got_raw, list):
        got = {str(a).strip().lower() for a in got_raw}
    elif isinstance(got_raw, str):
        got = {got_raw.strip().lower()}
    if got:
        frac = len(got & want) / max(len(want), 1)
        score += 0.25 * frac * (1.0 if got <= want else 0.5)  # 0.25 max; extras halve it
        extras = got - want
        if extras:
            detail.append(f"compromised_accounts extras={sorted(extras)}")
        missing = want - got
        if missing:
            detail.append(f"compromised_accounts missing={sorted(missing)}")
    else:
        detail.append("compromised_accounts missing/empty")
    score = min(score, 1.0)
    return score, "; ".join(detail) or "attribution correct"


def check_r2(f, gt):
    """Temporal correctness (UTC)."""
    detail = []
    score = 0.0
    if norm_str(f.get("incident_date_utc")) == gt["incident_date_utc"]:
        score += 0.25
    else:
        detail.append(f"incident_date_utc={f.get('incident_date_utc')!r} (expected {gt['incident_date_utc']})")

    win = f.get("attack_window_utc")
    if not isinstance(win, dict):
        detail.append("attack_window_utc missing/not an object")
        return score, "; ".join(detail)
    tol = timedelta(seconds=120)
    for key, expect_key, label in (("start", "window_start_utc", "start"),
                                   ("end", "window_end_utc", "end")):
        got_dt = parse_instant(win.get(key))
        expect_dt = parse_instant(gt[expect_key])
        if got_dt and expect_dt and abs(got_dt - expect_dt) <= tol:
            score += 0.375
        else:
            detail.append(f"window {label}={win.get(key)!r} (expected ~{gt[expect_key]})")
    return score, "; ".join(detail) or "temporal fields correct"


def check_r3(f, gt):
    """Exact metric counts."""
    fields = ["primary_ip_request_count", "failed_login_attempts",
              "successful_logins_from_attackers", "attack_source_ip_count",
              "web_5xx_count", "ssh_failed_password_lines",
              "ssh_distinct_source_ips", "ssh_failed_from_primary_ip",
              "app_error_entries"]
    bad = []
    n_ok = 0
    for k in fields:
        if norm_int(f.get(k)) == gt[k]:
            n_ok += 1
        else:
            bad.append(f"{k}={f.get(k)!r} (expected {gt[k]})")
    return n_ok / len(fields), ("; ".join(bad) if bad else "all 9 metrics exact")


def main():
    per_item = {}
    checks = []
    weights = {"R1": 0.25, "R2": 0.18, "R3": 0.27}

    try:
        gt = recompute_ground_truth()
    except Exception as e:  # never crash the verifier
        gt = dict(FALLBACK)
        sys.stderr.write(f"ground-truth recompute failed, using fallback: {e}\n")

    findings = None
    try:
        findings = json.load(open(FINDINGS_PATH, encoding="utf-8"))
        if not isinstance(findings, dict):
            raise ValueError("findings.json is not a JSON object")
    except Exception as e:
        for rid in weights:
            per_item[rid] = 0.0
            checks.append({"id": rid, "weight": weights[rid], "score": 0.0,
                           "detail": f"cannot load {FINDINGS_PATH}: {e}"})
    if findings is not None:
        for rid, fn in (("R1", check_r1), ("R2", check_r2), ("R3", check_r3)):
            try:
                s, d = fn(findings, gt)
            except Exception as e:
                s, d = 0.0, f"check error: {e}"
            per_item[rid] = round(s, 4)
            checks.append({"id": rid, "weight": weights[rid], "score": round(s, 4),
                           "detail": d})

    total_w = sum(weights[r] for r in per_item) or 1.0
    score = sum(per_item[r] * weights[r] for r in per_item) / total_w
    out = {"per_item": per_item, "checks": checks, "score": round(score, 4)}
    print(json.dumps(out))
    sys.exit(0)


if __name__ == "__main__":
    main()
