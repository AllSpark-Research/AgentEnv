#!/usr/bin/env python3
"""Deterministic verifier for the Nova Trail Outfitters media-handoff task.

Run from the solver's final workspace root:
    python3 verify.py
Prints exactly one JSON line and always exits 0.
"""

import json
import os
import sys

WEIGHTS = {
    "deliverables_format_dimensions": 0.30,
    "hard_constraints_size_metadata_alpha": 0.30,
    "report_fidelity": 0.25,
}
BUDGET = 1050000

# Ground truth from the frozen blueprint (derived from manifest/site_assets.csv +
# policy/media_standards.md precedence rules).
EXPECTED = {
    "hero_banner": {"src": "assets_raw/hero_banner.tiff",
                    "formats": {"WEBP"}, "edge": 1600, "cap": 230000},
    "product_front": {"src": "assets_raw/product_front.png",
                      "formats": {"WEBP"}, "edge": 1200, "cap": 200000},
    "product_side": {"src": "assets_raw/product_side.bmp",
                     "formats": {"WEBP"}, "edge": 1200, "cap": 80000},
    "team_photo": {"src": "assets_raw/team_photo.jpg",
                   "formats": {"WEBP"}, "edge": 1400, "cap": 160000},
    "press_release_photo": {"src": "assets_raw/press_release_photo.tiff",
                            "formats": {"JPEG"}, "edge": 2000, "cap": 350000},
    "fallback_banner": {"src": "assets_raw/fallback_banner.bmp",
                        "formats": {"WEBP"}, "edge": 1920, "cap": 125000},
    "logo": {"src": "assets_raw/logo.png",
             "formats": {"WEBP", "PNG"}, "edge": 400, "cap": 40000, "alpha": True},
    "ui_icons": {"src": "assets_raw/ui_icons.png",
                 "formats": {"PNG"}, "edge": None, "cap": 5500, "alpha": True},
    "bg_tile": {"src": "assets_raw/bg_tile.gif",
                "formats": {"PNG"}, "edge": None, "cap": 5000},
}
CORRUPT_STEM = "corrupt_export"
CORRUPT_SRC = f"assets_raw/{CORRUPT_STEM}.png"
ALL_SOURCES = [v["src"] for v in EXPECTED.values()] + [CORRUPT_SRC]
IMG_EXTS = {".webp", ".png", ".jpg", ".jpeg", ".gif"}

try:
    from PIL import Image
except Exception:  # library missing -> everything zero, still emits JSON
    Image = None


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def load_img(path):
    if Image is None:
        return None
    def _f():
        im = Image.open(path)
        im.load()
        return im
    return safe(_f)


def find_output(stem):
    """Locate delivered file optimized/<stem>.<img ext>; only opens files with image extensions."""
    if not os.path.isdir("optimized"):
        return None
    for f in os.listdir("optimized"):
        p = os.path.join("optimized", f)
        b, ext = os.path.splitext(f)
        if b == stem and ext.lower() in IMG_EXTS and os.path.isfile(p):
            return p
    return None


def original_longest(src):
    if Image is None:
        return None
    im = safe(lambda: Image.open(src))
    return max(im.size) if im is not None else None


def check_delivery():
    """R1: correct resolved format, edge cap respected, no upscaling, no corrupt output."""
    results, notes = [], []
    for stem, spec in EXPECTED.items():
        path = find_output(stem)
        if path is None or Image is None:
            results.append(0.0)
            notes.append(f"{stem}: missing")
            continue
        im = load_img(path)
        if im is None:
            results.append(0.0)
            notes.append(f"{stem}: unreadable")
            continue
        fmt_ok = (im.format or "").upper() in spec["formats"]
        longest = max(im.size)
        orig_longest = original_longest(spec["src"])
        edge_ok = True
        if spec["edge"] is not None:
            edge_ok = longest <= spec["edge"]
        if orig_longest is not None:
            edge_ok = edge_ok and longest <= orig_longest  # never upscale
        ok = fmt_ok and edge_ok
        results.append(1.0 if ok else 0.0)
        if not ok:
            notes.append(
                f"{stem}: format={im.format} allowed={sorted(spec['formats'])} "
                f"longest={longest} cap={spec['edge']} original={orig_longest}")
    # corrupt asset must NOT have a delivered file
    bad = find_output(CORRUPT_STEM)
    results.append(1.0 if bad is None else 0.0)
    if bad is not None:
        notes.append("corrupt_export has an output file (should not be fabricated)")
    score = sum(results) / len(results)
    detail = f"{sum(results)}/{len(results)} delivery checks passed"
    if notes:
        detail += " | " + "; ".join(notes[:6])
    return score, detail


def has_metadata(path):
    """EXIF (incl. GPS), XMP, or comment metadata present."""
    if Image is None:
        return True
    im = safe(lambda: Image.open(path))
    if im is None:
        return True
    exif = safe(lambda: im.getexif())
    if exif and len(exif) > 0:
        return True
    for key in ("exif", "xmp", "XML:com.adobe.xmp", "comment"):
        if key in im.info:
            return True
    return False


def has_real_alpha(path):
    if Image is None:
        return False
    im = load_img(path)
    if im is None or "A" not in im.getbands():
        return False
    return safe(lambda: im.getchannel("A").getextrema()[0], 255) < 100


def check_constraints():
    """R2: byte caps, global budget, metadata stripped, alpha preserved."""
    # per-asset byte caps
    caps = []
    for stem, spec in EXPECTED.items():
        path = find_output(stem)
        caps.append(1.0 if (path and os.path.getsize(path) <= spec["cap"]) else 0.0)
    caps_mean = sum(caps) / len(caps)

    # global budget over the whole optimized/ folder
    budget_ok = 0.0
    if os.path.isdir("optimized"):
        total = sum(os.path.getsize(os.path.join("optimized", f))
                    for f in os.listdir("optimized")
                    if os.path.isfile(os.path.join("optimized", f)))
        budget_ok = 1.0 if total <= BUDGET else 0.0

    # metadata stripped
    meta = []
    for stem in EXPECTED:
        path = find_output(stem)
        meta.append(0.0 if (path is None or has_metadata(path)) else 1.0)
    meta_mean = sum(meta) / len(meta)

    # alpha preserved where required
    alpha = []
    for stem, spec in EXPECTED.items():
        if not spec.get("alpha"):
            continue
        path = find_output(stem)
        alpha.append(1.0 if (path and has_real_alpha(path)) else 0.0)
    alpha_mean = sum(alpha) / len(alpha) if alpha else 1.0

    score = (caps_mean + budget_ok + meta_mean + alpha_mean) / 4.0
    detail = (f"caps={caps_mean:.2f} budget={'ok' if budget_ok else 'FAIL'} "
              f"metadata_stripped={meta_mean:.2f} alpha={alpha_mean:.2f}")
    return score, detail


def norm_fmt(s):
    s = str(s or "").strip().lower()
    return "jpeg" if s == "jpg" else s


def check_report():
    """R3: conversion_report.json schema + fidelity against the filesystem."""
    try:
        with open("conversion_report.json") as f:
            rep = json.load(f)
    except Exception as e:
        return 0.0, f"unparseable report: {e}"

    sub = []
    # structure
    struct_ok = (isinstance(rep, dict) and isinstance(rep.get("assets"), list)
                 and isinstance(rep.get("summary"), dict)
                 and all(k in rep["summary"] for k in
                         ("converted", "failed", "total_source_bytes", "total_output_bytes")))
    sub.append((0.2, 1.0 if struct_ok else 0.0))
    if not struct_ok:
        return 0.2 * sub[0][1], "missing assets/summary structure"

    assets = rep["assets"]
    by_src = {}
    for a in assets:
        if isinstance(a, dict) and "source" in a:
            by_src[os.path.basename(str(a["source"]))] = a

    # exact coverage of the 10 manifest sources
    want = {os.path.basename(s) for s in ALL_SOURCES}
    have = set(by_src)
    coverage = len(want & have) / len(want) if want else 0.0
    if want != have:
        coverage = min(coverage, 0.5)  # extra/missing rows breach the contract
    sub.append((0.2, coverage))

    # statuses
    statuses = 0.0
    for stem, spec in EXPECTED.items():
        a = by_src.get(os.path.basename(spec["src"]), {})
        statuses += 1.0 if a.get("status") == "converted" else 0.0
    a = by_src.get(os.path.basename(CORRUPT_SRC), {})
    statuses += 1.0 if a.get("status") == "failed" else 0.0
    sub.append((0.2, statuses / len(ALL_SOURCES)))

    # value accuracy for converted rows
    acc = []
    for stem, spec in EXPECTED.items():
        a = by_src.get(os.path.basename(spec["src"]))
        if not a or a.get("status") != "converted":
            acc.append(0.0)
            continue
        out = a.get("output")
        ok = bool(out) and os.path.isfile(str(out))
        if ok:
            actual_size = os.path.getsize(str(out))
            ok = (a.get("output_bytes") == actual_size
                  and a.get("source_bytes") == os.path.getsize(spec["src"]))
        if ok and Image is not None:
            im = safe(lambda: Image.open(str(out)))
            if im is None:
                ok = False
            else:
                w, h = im.size
                ok = (abs(int(a.get("width") or -999) - w) <= 2
                      and abs(int(a.get("height") or -999) - h) <= 2
                      and norm_fmt(a.get("resolved_format")) == norm_fmt(im.format))
        acc.append(1.0 if ok else 0.0)
    sub.append((0.25, sum(acc) / len(acc) if acc else 0.0))

    # summary consistency
    try:
        conv = [a for a in assets if isinstance(a, dict) and a.get("status") == "converted"]
        fail = [a for a in assets if isinstance(a, dict) and a.get("status") == "failed"]
        s = rep["summary"]
        ok = (s["converted"] == len(conv) == 9 and s["failed"] == len(fail) == 1)
        ts = sum(int(x.get("source_bytes") or 0) for x in assets if isinstance(x, dict))
        to = sum(int(x.get("output_bytes") or 0) for x in conv)
        ok = ok and s["total_source_bytes"] == ts and s["total_output_bytes"] == to
        actual_raw = sum(os.path.getsize(p) for p in ALL_SOURCES if os.path.isfile(p))
        ok = ok and ts == actual_raw
        sub.append((0.15, 1.0 if ok else 0.0))
    except Exception:
        sub.append((0.15, 0.0))

    score = sum(w * v for w, v in sub)
    detail = ("structure={:.1f} coverage={:.2f} statuses={:.2f} "
              "accuracy={:.2f} summary={:.1f}".format(*(v for _, v in sub)))
    return score, detail


def main():
    per_item, checks = {}, []
    for rid, fn in (("deliverables_format_dimensions", check_delivery),
                    ("hard_constraints_size_metadata_alpha", check_constraints),
                    ("report_fidelity", check_report)):
        try:
            score, detail = fn()
        except Exception as e:
            score, detail = 0.0, f"checker crashed: {e}"
        score = max(0.0, min(1.0, float(score)))
        per_item[rid] = score
        checks.append({"id": rid, "weight": WEIGHTS[rid], "score": score, "detail": detail})
    total_w = sum(WEIGHTS.values())
    overall = sum(WEIGHTS[c["id"]] * c["score"] for c in checks) / total_w
    print(json.dumps({"per_item": per_item, "checks": checks, "score": round(overall, 4)}))
    sys.exit(0)


if __name__ == "__main__":
    main()
