#!/usr/bin/env python3
"""Deterministic verifier for the Meridian Analytics OIDC remediation task.

Run with cwd = solver's final workspace:  python3 verify.py
Implements the deterministic rubric items from eval_spec.json.
"""
import json
import re
import sys

# ------------------------------------------------------------ ground truth
PINS = {
    "aws-actions/configure-aws-credentials": "c25c4db6602bf1882cafb007f8d2e75d91c33366",
    "google-github-actions/auth": "20f0fd44ad1e75bbbb028ff440a98bd56452bb45",
    "azure/login": "6ec18d2562efdc25fcc543b11dd71a1ba7157be5",
}
ARN_STAGING = "arn:aws:iam::111122223333:role/github-actions-staging-deploy"
ARN_PROD = "arn:aws:iam::444455556666:role/github-actions-prod-deploy"
ARN_BACKUP = "arn:aws:iam::444455556666:role/github-actions-prod-backup"
WIF_ML = "projects/583920174655/locations/global/workloadIdentityPools/github-actions/providers/github"
SA_ML = "github-ml-training@meridian-ml-prod.iam.gserviceaccount.com"
WIF_DATA = "projects/910284756312/locations/global/workloadIdentityPools/github-actions/providers/github"
SA_DATA = "github-data-export@meridian-data-prod.iam.gserviceaccount.com"
AZ = {
    "client-id": "05032e4e-d1be-427c-8483-877103465e47",
    "tenant-id": "c32cca8c-8436-425f-8ea8-685e3adb1549",
    "subscription-id": "1d8ceee9-324b-4f9e-baaf-f72fefc6fdf5",
}

BANNED_PATTERNS = [
    r"AWS_ACCESS_KEY_ID",
    r"AWS_SECRET_ACCESS_KEY",
    r"AWS_SESSION_TOKEN",
    r"AZURE_CLIENT_SECRET",
    r"AZURE_CREDENTIALS",
    r"GCP_SERVICE_ACCOUNT_KEY",
    r"GOOGLE_CREDENTIALS",
    r"(?mi)^\s*aws-access-key-id\s*:",
    r"(?mi)^\s*aws-secret-access-key\s*:",
    r"credentials_json\s*:",
    r"(?mi)^\s*creds\s*:",
    r"activate-service-account\s+--key-file",
]

WORKFLOW_EXPECTATIONS = {
    ".github/workflows/deploy-aws-prod.yml": {
        "role": ARN_PROD,
        "sentinels": ["aws s3 sync", "cloudfront create-invalidation"],
    },
    ".github/workflows/deploy-aws-staging.yml": {
        "role": ARN_STAGING,
        "sentinels": ["s3://meridian-staging-web"],
    },
    ".github/workflows/ml-training-gcp.yml": {
        "wif": WIF_ML,
        "sa": SA_ML,
        "sentinels": ["gcloud ai custom-jobs create"],
    },
    ".github/workflows/azure-webapp-deploy.yml": {
        "azure": AZ,
        "sentinels": ["az webapp deployment source config-zip"],
    },
    ".github/workflows/nightly-backup-aws.yml": {
        "role": ARN_BACKUP,
        "sentinels": ["create-db-snapshot"],
    },
    ".github/workflows/data-export-gcp.yml": {
        "wif": WIF_DATA,
        "sa": SA_DATA,
        "sentinels": ["bq extract"],
        "must_add_gcp_auth": True,
    },
}
PRESERVE_HASHES = {
    ".github/workflows/ci.yml": "9b5e8bb9ef158a84c82344f12ba91f50790bc0785a4546fcaf454d659d3bfd77",
    "archived/2023/legacy-aws-deploy.yml": "e40e01c3f4dc8243c683ab4dc1aa70507682f5807b7e470c5c6db3bf85764c22",
    "security/action-pins.yml": "fb3b1cb01c8880646c2c4014bc2f043c29267f6b7c5d4c47068e3fc8e9488ed6",
}
BASELINE = {"workflows_scanned": 8, "workflows_flagged": 5, "critical_count": 2, "warn_count": 1}
AFTER = {"workflows_scanned": 8, "workflows_flagged": 0, "critical_count": 0, "warn_count": 0}


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def load_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load_yaml(path):
    import yaml
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def auth_steps(data):
    out = []
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, dict):
        return out
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if not isinstance(uses, str):
                continue
            name = uses.split("@", 1)[0].strip().lower()
            if name in PINS:
                out.append((job_name, job, step, name))
    return out


def banned_hits(text):
    return [p for p in BANNED_PATTERNS if re.search(p, text)]

# ------------------------------------------------------------ D1
def check_oidc_compliance():
    per_file = {}
    notes = []
    for path, exp in WORKFLOW_EXPECTATIONS.items():
        text = safe(lambda: load_text(path))
        if text is None:
            per_file[path] = 0.0
            notes.append(path + ": missing")
            continue
        data = safe(lambda: load_yaml(path), {})
        steps = auth_steps(data)

        subs = []
        hits = banned_hits(text)
        subs.append((not hits, "static-cred patterns: " + (str(hits) if hits else "none")))
        if steps:
            bad = []
            for _, _, step, name in steps:
                uses = step["uses"]
                ref = ""
                if "@" in uses:
                    ref = uses.split("@", 1)[1].split()[0].split("#")[0]
                if ref != PINS[name]:
                    bad.append(name + "@" + ref)
            subs.append((not bad, "pin mismatches: " + (str(bad) if bad else "none")))
        else:
            subs.append((False, "no cloud auth step found"))

        val_ok, val_note = True, []
        if "role" in exp:
            found = any(
                isinstance(s.get("with"), dict) and s["with"].get("role-to-assume") == exp["role"]
                for _, _, s, n in steps if n == "aws-actions/configure-aws-credentials"
            )
            val_ok = val_ok and found
            if not found:
                val_note.append("role-to-assume wrong/missing")
        if "wif" in exp:
            found = any(
                isinstance(s.get("with"), dict)
                and s["with"].get("workload_identity_provider") == exp["wif"]
                and s["with"].get("service_account") == exp["sa"]
                for _, _, s, n in steps if n == "google-github-actions/auth"
            )
            val_ok = val_ok and found
            if not found:
                val_note.append("WIF provider/service account wrong/missing")
        if exp.get("must_add_gcp_auth") and not any(n == "google-github-actions/auth" for _, _, _, n in steps):
            val_ok = False
            val_note.append("google auth step not added")
        if "azure" in exp:
            found = any(
                isinstance(s.get("with"), dict)
                and s["with"].get("client-id") == exp["azure"]["client-id"]
                and s["with"].get("tenant-id") == exp["azure"]["tenant-id"]
                and s["with"].get("subscription-id") == exp["azure"]["subscription-id"]
                for _, _, s, n in steps if n == "azure/login"
            )
            val_ok = val_ok and found
            if not found:
                val_note.append("azure OIDC ids wrong/missing")
        subs.append((val_ok, "; ".join(val_note) if val_note else "values ok"))

        per_file[path] = sum(1 for ok, _ in subs if ok) / len(subs)
        for ok, note in subs:
            if not ok:
                notes.append(path + ": " + note)

    score = sum(per_file.values()) / len(per_file)
    short = {k.split("/")[-1]: round(v, 3) for k, v in per_file.items()}
    return score, "per-file=" + json.dumps(short) + "; issues: " + ("; ".join(notes) if notes else "none")


# ------------------------------------------------------------ D2
def check_permission_scoping():
    import glob
    ok_jobs = 0
    bad_jobs = []
    files = sorted(glob.glob(".github/workflows/*.yml") + glob.glob(".github/workflows/*.yaml"))
    for path in files:
        data = safe(lambda: load_yaml(path), {})
        for job_name, job, step, _ in auth_steps(data):
            perms = job.get("permissions")
            good = isinstance(perms, dict) and str(perms.get("id-token", "")).strip() == "write"
            if good:
                ok_jobs += 1
            else:
                bad_jobs.append(path + ":" + str(job_name))
    total = ok_jobs + len(bad_jobs)
    if total == 0:
        return 0.0, "no cloud-auth jobs found at all"
    return ok_jobs / total, "job-level id-token write: %d/%d; missing: %s" % (ok_jobs, total, bad_jobs)

# ------------------------------------------------------------ D3
def check_audit_evidence():
    parts = []

    def summary_score(path, expected):
        obj = safe(lambda: json.loads(load_text(path)))
        if not isinstance(obj, dict):
            return 0.0, path + " missing or not JSON"
        summ = obj.get("summary")
        if not isinstance(summ, dict):
            return 0.0, path + " has no summary object"
        got = sum(1 for k, v in expected.items() if summ.get(k) == v)
        note = path + " " + ", ".join("%s=%s(want %s)" % (k, summ.get(k), v) for k, v in expected.items())
        return got / len(expected), note

    s, n = summary_score("audit/before.json", BASELINE)
    parts.append((s, n, 0.4))
    s, n = summary_score("audit/after.json", AFTER)
    parts.append((s, n, 0.25))

    def rescan():
        import subprocess
        env = {
            "WORKFLOW_GLOB": ".github/workflows/*.y*ml",
            "OUTPUT_FORMAT": "json",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": "/tmp",
        }
        proc = subprocess.run(
            ["bash", "_skill_ref/scripts/oidc-hardening-audit.sh"],
            cwd=".", env=env, capture_output=True, text=True, timeout=120,
        )
        return json.loads(proc.stdout)["summary"]

    summ = safe(rescan)
    if summ is None:
        parts.append((0.0, "independent re-scan failed", 0.35))
    else:
        clean = summ.get("workflows_flagged") == 0 and summ.get("critical_count") == 0
        scanned_ok = summ.get("workflows_scanned") == 8
        score = (0.7 if clean else 0.0) + (0.3 if scanned_ok else 0.0)
        parts.append((score, "independent re-scan: " + json.dumps(summ), 0.35))

    total = sum(s * w for s, _, w in parts) / sum(w for _, _, w in parts)
    return total, " || ".join(n for _, n, _ in parts)


# ------------------------------------------------------------ D4
def check_scope_preservation():
    import hashlib
    results = []
    for path, want in PRESERVE_HASHES.items():
        got = safe(lambda: hashlib.sha256(load_text(path).encode()).hexdigest())
        ok = got == want
        results.append((ok, path + (" unchanged" if ok else " MODIFIED (must be untouched)")))
    for path, exp in WORKFLOW_EXPECTATIONS.items():
        text = safe(lambda: load_text(path), "") or ""
        ok = all(s in text for s in exp["sentinels"])
        if ok:
            results.append((True, path + " functional steps preserved"))
        else:
            lost = [s for s in exp["sentinels"] if s not in text]
            results.append((False, path + " functional steps LOST: " + str(lost)))
    rel = safe(lambda: load_text(".github/workflows/release.yml"), "") or ""
    ok = PINS["aws-actions/configure-aws-credentials"] in rel and ARN_PROD in rel
    results.append((ok, "release.yml exemplar intact" if ok else "release.yml exemplar damaged"))
    ok_count = sum(1 for ok, _ in results if ok)
    return ok_count / len(results), " ; ".join(n for _, n in results)


# ------------------------------------------------------------ main
def main():
    checks = []

    def run(rid, weight, fn):
        try:
            score, detail = fn()
            score = max(0.0, min(1.0, float(score)))
        except Exception as exc:
            score, detail = 0.0, "check crashed: %r" % exc
        checks.append({"id": rid, "weight": weight, "score": round(score, 4), "detail": detail})

    run("D_oidc_compliance", 0.40, check_oidc_compliance)
    run("D_permission_scoping", 0.15, check_permission_scoping)
    run("D_audit_evidence", 0.10, check_audit_evidence)
    run("D_scope_preservation", 0.10, check_scope_preservation)

    total_weight = sum(c["weight"] for c in checks)
    score = sum(c["score"] * c["weight"] for c in checks) / total_weight if total_weight else 0.0
    print(json.dumps({
        "per_item": {c["id"]: c["score"] for c in checks},
        "checks": checks,
        "score": round(score, 4),
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
