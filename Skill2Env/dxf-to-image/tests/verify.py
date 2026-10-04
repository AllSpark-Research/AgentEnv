#!/usr/bin/env python3
"""Deterministic verifier for the DXF review-package task.

Run from the solver's final workspace: python3 verify.py
Prints exactly one JSON line and exits 0.
"""
import json
import os
import re

REQUIRED_FIELDS = ["file", "status", "entity_count", "layers", "extents", "preview", "notes"]

EXPECTED_STATUS = {
    "site_plan_R2.dxf": {"superseded"},
    "site_plan_R3.dxf": {"superseded"},
    "site_plan_R3a.dxf": {"ok"},
    "annex_building.dxf": {"ok"},
    "utilities_R1.dxf": {"ok"},
    "landscape_R4.dxf": {"recovered", "ok"},
    "drainage_R1.dxf": {"failed"},
}

GT = {
    "annex_building.dxf": {
        "entity_count": 18,
        "layers": ["DOORS", "FURN", "TEXT", "WALLS"],
        "extents": {"min_x": 0.0, "min_y": 0.0, "max_x": 41.277, "max_y": 28.1},
    },
    "site_plan_R2.dxf": {
        "entity_count": 17,
        "layers": ["BLDG", "LANDSCAPE", "PROP", "ROAD", "TEXT"],
        "extents": {"min_x": 0.0, "min_y": -12.628, "max_x": 120.0, "max_y": 80.0},
    },
    "site_plan_R3.dxf": {
        "entity_count": 30,
        "layers": ["BLDG", "LANDSCAPE", "PROP", "ROAD", "TEXT"],
        "extents": {"min_x": 0.0, "min_y": -12.628, "max_x": 120.0, "max_y": 80.0},
    },
    "site_plan_R3a.dxf": {
        "entity_count": 35,
        "layers": ["BLDG", "LANDSCAPE", "PROP", "ROAD", "TEXT"],
        "extents": {"min_x": 0.0, "min_y": -12.628, "max_x": 120.0, "max_y": 80.0},
    },
    "utilities_R1.dxf": {
        "entity_count": 10,
        "layers": ["ELEC", "MH", "SEWER", "TEXT", "WATER"],
        "extents": {"min_x": 0.0, "min_y": 0.0, "max_x": 100.0, "max_y": 84.5},
    },
    "landscape_R4.dxf": {
        "entity_count": 9,
        "layers": ["PATH", "PLANT", "TEXT", "WATER"],
        "extents": {"min_x": 0.0, "min_y": 0.0, "max_x": 74.0, "max_y": 72.5},
    },
}

EXPECTED_PREVIEWS = ["annex_building.png", "landscape_R4.png", "site_plan_R3a.png", "utilities_R1.png"]
FORBIDDEN_PREVIEWS = ["site_plan_R2.png", "site_plan_R3.png", "drainage_R1.png"]
WIDTH_MIN, WIDTH_MAX = 1080, 1320
NONBLANK_FRAC = 0.001
SVG_PATH_MIN, SVG_PATH_MAX = 33, 37  # R3a signature = 35; R3=30 and R2=17 fall outside


def load_manifest():
    try:
        with open("manifest.json", encoding="utf-8") as f:
            m = json.load(f)
        files = m.get("files")
        if not isinstance(files, list):
            return None, "manifest.json has no 'files' array"
        return m, None
    except Exception as e:
        return None, f"manifest.json unreadable: {e}"


def index_by_basename(files):
    idx = {}
    for e in files:
        if isinstance(e, dict) and isinstance(e.get("file"), str):
            idx[os.path.basename(e["file"])] = e
    return idx


def check_manifest_basics():
    m, err = load_manifest()
    if err:
        return 0.0, err
    files = m["files"]
    idx = index_by_basename(files)
    missing = [f for f in EXPECTED_STATUS if f not in idx]
    schema_ok = all(
        all(k in idx[f] for k in REQUIRED_FIELDS) for f in EXPECTED_STATUS if f in idx
    )
    structure = (1.0 - len(missing) / len(EXPECTED_STATUS)) * (1.0 if schema_ok else 0.5)
    correct = 0
    detail = []
    for f, allowed in EXPECTED_STATUS.items():
        e = idx.get(f)
        if e is None:
            detail.append(f"{f}:missing")
            continue
        st = str(e.get("status", "")).strip().lower()
        if st in allowed:
            correct += 1
        else:
            detail.append(f"{f}:{st}")
    score = 0.3 * structure + 0.7 * (correct / len(EXPECTED_STATUS))
    return round(score, 4), "statuses ok=%d/6%s" % (correct, ("; " + ",".join(detail)) if detail else "")


def close(a, b):
    try:
        a, b = float(a), float(b)
    except Exception:
        return False
    return abs(a - b) <= max(0.25, 0.02 * abs(b))


def check_manifest_metrics():
    m, err = load_manifest()
    if err:
        return 0.0, err
    idx = index_by_basename(m["files"])
    per_file = []
    notes = []
    for f, gt in GT.items():
        e = idx.get(f)
        if e is None:
            per_file.append(0.0)
            notes.append(f"{f}:missing-entry")
            continue
        s = 0.0
        ec = e.get("entity_count")
        if isinstance(ec, bool) is False and isinstance(ec, int) and ec == gt["entity_count"]:
            s += 0.4
        else:
            notes.append(f"{f}:entity_count={ec!r}!={gt['entity_count']}")
        layers = e.get("layers")
        if isinstance(layers, list) and sorted(str(x).upper() for x in layers) == gt["layers"]:
            s += 0.3
        else:
            notes.append(f"{f}:layers={layers!r}")
        ext = e.get("extents")
        if isinstance(ext, dict) and all(close(ext.get(k, None), gt["extents"][k]) for k in
                                          ("min_x", "min_y", "max_x", "max_y")):
            s += 0.3
        else:
            notes.append(f"{f}:extents={ext!r}")
        per_file.append(s)
    return round(sum(per_file) / len(per_file), 4), "; ".join(notes) if notes else "all metrics match"


def frac_nonwhite(path):
    from PIL import Image
    import numpy as np
    im = Image.open(path).convert("L")
    a = np.asarray(im, dtype=np.float32)
    return float((a < 245).mean())


def check_previews():
    if not os.path.isdir("previews"):
        return 0.0, "previews/ directory missing"
    per = []
    notes = []
    for name in EXPECTED_PREVIEWS:
        p = os.path.join("previews", name)
        s = 0.0
        if os.path.isfile(p):
            s += 0.25
            try:
                from PIL import Image
                im = Image.open(p)
                if WIDTH_MIN <= im.width <= WIDTH_MAX:
                    s += 0.30
                else:
                    notes.append(f"{name}:width={im.width}")
                frac = frac_nonwhite(p)
                if frac > NONBLANK_FRAC:
                    s += 0.45
                else:
                    notes.append(f"{name}:blank(frac={frac:.5f})")
            except Exception as ex:
                notes.append(f"{name}:unreadable:{ex}")
        else:
            notes.append(f"{name}:missing")
        per.append(s)
    score = sum(per) / len(per)
    penalty = 0.0
    for name in FORBIDDEN_PREVIEWS:
        if os.path.isfile(os.path.join("previews", name)):
            penalty += 0.10
            notes.append(f"forbidden:{name}")
    score = max(0.0, score - penalty)
    return round(score, 4), "; ".join(notes) if notes else "4 previews present, sized, non-blank"


def check_svg():
    p = "web/site_plan.svg"
    if not os.path.isfile(p):
        return 0.0, "web/site_plan.svg missing"
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception as e:
        return 0.0, f"unreadable: {e}"
    if "<svg" not in text:
        return 0.0, "not an SVG document"
    score = 0.4
    n = len(re.findall(r"<path[\s>]", text))
    if SVG_PATH_MIN <= n <= SVG_PATH_MAX:
        score += 0.6
        return score, f"valid SVG, {n} paths (R3a signature)"
    return score, f"valid SVG but {n} paths (expected ~35 for R3a; R3 would be 30, R2 would be 17)"


ITEMS = {
    "manifest_basics": (0.20, check_manifest_basics),
    "manifest_metrics": (0.25, check_manifest_metrics),
    "previews": (0.30, check_previews),
    "svg_revision": (0.15, check_svg),
}


def main():
    per_item = {}
    checks = []
    total_weight = 0.0
    weighted = 0.0
    for rid, (w, fn) in ITEMS.items():
        try:
            score, detail = fn()
        except Exception as e:
            score, detail = 0.0, f"check crashed: {e}"
        score = max(0.0, min(1.0, float(score)))
        per_item[rid] = score
        checks.append({"id": rid, "weight": w, "score": score, "detail": detail})
        total_weight += w
        weighted += w * score
    out = {
        "per_item": per_item,
        "checks": checks,
        "score": round(weighted / total_weight, 4) if total_weight else 1.0,
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
