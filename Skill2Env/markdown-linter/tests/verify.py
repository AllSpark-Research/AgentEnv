#!/usr/bin/env python3
"""Deterministic verifier for the AuroraKit docs link-integrity task.

Run with cwd = solver's final workspace. Prints exactly one JSON line.
"""
import hashlib
import json
import os
import re
import sys

REPO = "aurorakit-docs"

# ---------------------------------------------------------------- ground truth
BASELINE_FILES_SCANNED = 20
BASELINE_BROKEN_LINKS = 9
ADDITIONAL_BROKEN = 3

# (file relative to REPO, from-as-written, to as repo-relative path)
EXPECTED_FIXES = [
    ("README.md", "docs/getting-started/installation.md", "docs/guides/install.md"),
    ("README.md", "docs/legacy/faq.md", "docs/guides/troubleshooting.md"),
    ("CONTRIBUTING.md", "docs/style-guide.md", "docs/style/editorial-guide.md"),
    ("CONTRIBUTING.md", ".github/ISSUE_TEMPLATE/bug-report.md", "templates/bug-report.md"),
    ("docs/README.md", "guides/quickstart.md", "docs/guides/start-here.md"),
    ("docs/README.md", "API/Authentication.MD", "docs/api/authentication.md"),
    ("docs/guides/troubleshooting.md", "../reference/error-codes.md", "docs/api/error-codes.md"),
    ("docs/architecture/overview.md", "../images/architecture.png", "docs/images/architecture-overview.png"),
    ("docs/ops/runbook.md", "/docs/oncall.md", "docs/ops/oncall-guide.md"),
    ("CHANGELOG.md", "docs/migration-guide.md", "docs/migration/moves-1.0.md"),
    ("docs/guides/configuration.md", "./config-schema.md", "docs/api/config-schema.md"),
    ("docs/api/authentication.md", "./cli-tokens.md", "docs/api/auth-tokens.md"),
]

# Number of links pointing at the OLD target in the pristine file
# (fix 12's old target also serves a second, legitimate CLI link).
ORIGINAL_OLD_COUNTS = {
    ("docs/api/authentication.md", "./cli-tokens.md"): 2,
}

INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
REF_DEF_RE = re.compile(r"^\s{0,3}\[([^\]^][^\]]*)\]:\s*(\S+)", re.MULTILINE)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def _hashes(paths):
    return {p: _sha256(os.path.join(REPO, p)) for p in paths}


# Hashes of files that must remain byte-identical, computed at authoring time.
# Keyed mapping is injected below by the build script; see _expected_hashes().
EXPECTED_HASHES = {
 "docs/api/auth-tokens.md": "5a16b5156183a21f5a55a871465502e2014408aa838fe15aa458d3d871443d23",
 "docs/api/cli-tokens.md": "51798270e1cb71bdecb4a038340a0ab7e95cbd3bf8e3c310cc46d408b9c68a0c",
 "docs/api/config-schema.md": "bcf6eb6042aa22dbbc0c6223555ba04eb8ff3bf57af557ddcaadab478e208f0b",
 "docs/api/error-codes.md": "991ca72db430b569c9e40adbc2a4acfab04dbd0b985c66be6cd2d417b6a3a555",
 "docs/guides/install.md": "dac934fd66c51ca2c1aaac7333b7837a083646243dfabafc3fd1849fe4ba0fe4",
 "docs/guides/start-here.md": "edd466c178da0aebbfd897a78a80207dd3f62f6c973e19409d3d30fe3aaf89a2",
 "docs/images/architecture-overview.png": "c414cd0e204de974f73753c7e28d7638e7b3691bb8b1a2bab6b25bb7fed7ce77",
 "docs/migration/moves-1.0.md": "1fd97470d430049a06a9aae514debfbf9e81cd248a09c6fd8203550041a6aeef",
 "docs/ops/oncall-guide.md": "890b32d0f3de73950756b2e613077ce34d6c4a2d65326c14b5ad226668930872",
 "docs/style/editorial-guide.md": "d0daee4efcab33e333f7d5641aced197c2e4391d58a20506841367f177d6dca4",
 "reports/triage-notes.md": "042144e34960f1582c9b2965a5f31c8ad330fabdded2ab93e8a92bb767a3d3e9",
 "templates/bug-report.md": "65320f7f324e3c4a9bea54ba370625e815491a1a349d246e0c94521b43aff93a"
}

ALL_ORIGINAL_FILES = sorted(set(EXPECTED_HASHES) | {f for f, _, _ in EXPECTED_FIXES})


def norm_target(t):
    t = t.split("#")[0].split("?")[0].strip()
    while t.startswith("./"):
        t = t[2:]
    if t.startswith("/"):
        t = t[1:]
    return t


def is_external(url):
    u = url.lower()
    return u.startswith(("http://", "https://", "mailto:", "ftp", "data:"))


def resolve_target(file_rel, target):
    t = norm_target(target)
    if not t:
        return None
    if target.strip().startswith("/"):
        return os.path.normpath(os.path.join(REPO, t))
    return os.path.normpath(os.path.join(REPO, os.path.dirname(file_rel), t))


def iter_md_files():
    for dirpath, _dirnames, filenames in os.walk(REPO):
        if not dirpath.startswith(REPO):
            continue
        for fn in filenames:
            if fn.endswith(".md"):
                yield os.path.relpath(os.path.join(dirpath, fn), REPO)


def collect_links(file_rel):
    """Return list of (raw_target) for inline links and reference defs."""
    path = os.path.join(REPO, file_rel)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return []
    targets = [m.group(2) for m in INLINE_LINK_RE.finditer(content)]
    targets += [m.group(2) for m in REF_DEF_RE.finditer(content)]
    return [t for t in targets if not is_external(t)]


# ------------------------------------------------------------------- checks
def check_integrity():
    """R-item: no remaining broken internal links; original files present."""
    try:
        if not os.path.isdir(REPO):
            return 0.0, "aurorakit-docs/ missing"
        missing = [f for f in ALL_ORIGINAL_FILES
                   if not os.path.exists(os.path.join(REPO, f))]
        remaining = []
        for rel in iter_md_files():
            for target in collect_links(rel):
                r = resolve_target(rel, target)
                if r and not os.path.exists(r):
                    remaining.append(f"{rel} -> {target}")
        exist_frac = 1.0 - len(missing) / max(1, len(ALL_ORIGINAL_FILES))
        link_frac = max(0.0, 1.0 - len(remaining) / 12.0)
        score = round(exist_frac * link_frac, 4)
        detail = (f"missing_files={missing[:4]} (n={len(missing)}); "
                  f"still_broken={remaining[:6]} (n={len(remaining)})")
        return score, detail
    except Exception as e:  # noqa: BLE001
        return 0.0, f"error: {e}"


def check_fix_correctness():
    """Each defective link redirected to exactly the correct target, in place."""
    try:
        correct = []
        wrong = []
        for file_rel, old_from, exp_to in EXPECTED_FIXES:
            path = os.path.join(REPO, file_rel)
            if not os.path.exists(path):
                wrong.append((file_rel, "file missing"))
                continue
            targets = collect_links(file_rel)
            resolved = {resolve_target(file_rel, t) for t in targets}
            exp_resolved = os.path.normpath(os.path.join(REPO, exp_to))
            has_new = exp_resolved in resolved
            old_norm = norm_target(old_from)
            old_now = sum(1 for t in targets if norm_target(t) == old_norm)
            old_max = ORIGINAL_OLD_COUNTS.get((file_rel, old_from), 1) - 1
            old_gone = old_now <= old_max
            if has_new and old_gone:
                correct.append(file_rel)
            else:
                wrong.append((file_rel,
                              f"has_new={has_new} old_gone={old_gone}"
                              f" old_remaining={old_now}"))
        score = round(len(correct) / len(EXPECTED_FIXES), 4)
        return score, f"correct={len(correct)}/12 wrong={wrong[:5]}"
    except Exception as e:  # noqa: BLE001
        return 0.0, f"error: {e}"


def check_audit_json():
    try:
        p = os.path.join(REPO, "link-audit.json")
        if not os.path.exists(p):
            return 0.0, "link-audit.json missing"
        data = json.load(open(p, "r", encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return 0.0, f"not parseable: {e}"
    try:
        score = 0.0
        notes = []
        fixes = data.get("fixes")
        if isinstance(fixes, list) and all(isinstance(x, dict) for x in fixes):
            score += 0.15
        else:
            notes.append("fixes not a list of objects")
            fixes = []
        baseline = data.get("baseline") or {}
        if baseline.get("files_scanned") == BASELINE_FILES_SCANNED:
            score += 0.15
        else:
            notes.append(f"files_scanned={baseline.get('files_scanned')!r}")
        if baseline.get("broken_links_found") == BASELINE_BROKEN_LINKS:
            score += 0.2
        else:
            notes.append(f"broken_links_found={baseline.get('broken_links_found')!r}")
        if data.get("additional_broken_references") == ADDITIONAL_BROKEN:
            score += 0.1
        else:
            notes.append(f"additional={data.get('additional_broken_references')!r}")

        matched = 0
        for file_rel, old_from, exp_to in EXPECTED_FIXES:
            old_norm = norm_target(old_from)
            exp_resolved = os.path.normpath(os.path.join(REPO, exp_to))
            hit = False
            for entry in fixes:
                f = str(entry.get("file", ""))
                f = f.split("aurorakit-docs/", 1)[-1].lstrip("./")
                if f != file_rel:
                    continue
                frm = norm_target(str(entry.get("from", "")))
                to = str(entry.get("to", ""))
                to_res = resolve_target(file_rel, to)
                if frm == old_norm and to_res == exp_resolved:
                    hit = True
                    break
            if hit:
                matched += 1
        score += 0.4 * matched / len(EXPECTED_FIXES)
        notes.append(f"fixes_matched={matched}/12")
        return round(score, 4), "; ".join(notes)
    except Exception as e:  # noqa: BLE001
        return 0.0, f"error: {e}"


def check_preservation():
    try:
        intact, touched = [], []
        for rel, h in EXPECTED_HASHES.items():
            p = os.path.join(REPO, rel)
            if os.path.exists(p) and _sha256(p) == h:
                intact.append(rel)
            else:
                touched.append(rel)
        score = round(len(intact) / max(1, len(EXPECTED_HASHES)), 4)
        return score, f"intact={len(intact)}/{len(EXPECTED_HASHES)} changed={touched[:6]}"
    except Exception as e:  # noqa: BLE001
        return 0.0, f"error: {e}"


CHECKS = {
    "docs_tree_link_integrity": (0.30, check_integrity),
    "fix_target_correctness": (0.28, check_fix_correctness),
    "audit_json": (0.14, check_audit_json),
    "preservation": (0.08, check_preservation),
}


def main():
    per_item, checks, total_w, acc = {}, [], 0.0, 0.0
    for cid, (w, fn) in CHECKS.items():
        try:
            s, detail = fn()
        except Exception as e:  # noqa: BLE001
            s, detail = 0.0, f"crash: {e}"
        s = max(0.0, min(1.0, s))
        per_item[cid] = s
        checks.append({"id": cid, "weight": w, "score": s, "detail": detail})
        total_w += w
        acc += w * s
    out = {"per_item": per_item, "checks": checks,
           "score": round(acc / total_w, 4) if total_w else 1.0}
    print(json.dumps(out))
    sys.exit(0)


if __name__ == "__main__":
    main()
