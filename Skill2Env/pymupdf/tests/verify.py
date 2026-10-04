#!/usr/bin/env python3
"""Deterministic verifier for the catalog preflight / change-review task.

Run as: python3 verify.py   (cwd = solver's final workspace)
Prints exactly one JSON line and exits 0.
"""
import json
import os
import sys

RESULT = {"per_item": {}, "checks": [], "score": 1.0}

WEIGHTS = {
    "changed_pages": 0.25,
    "preflight_page_geometry": 0.20,
    "undersized_images": 0.25,
    "previews": 0.15,
}

REPORT_PATH = "deliverables/preflight_report.json"
V3 = "incoming/catalog_v3.pdf"

EXPECTED_CHANGED = {3, 5, 6, 8}
EXPECTED_UNDERSIZED = {
    4: (600, 450, 150.0),
    5: (640, 480, 213.33),
    6: (1200, 900, 200.0),
}
EXPECTED_EMBEDDED = 6
EXPECTED_PAGES = 8
A4 = (595.2756, 841.8898)
LETTER = (612.0, 792.0)
EXPECTED_PREVIEWS = {
    "deliverables/previews/page-3.png": (3, 1275, 1650),
    "deliverables/previews/page-5.png": (5, 1275, 1650),
    "deliverables/previews/page-6.png": (6, 1275, 1650),
    "deliverables/previews/page-8.png": (8, 1241, 1754),
}


def add(item_id, score, detail):
    score = max(0.0, min(1.0, float(score)))
    RESULT["per_item"][item_id] = round(score, 4)
    RESULT["checks"].append(
        {"id": item_id, "weight": WEIGHTS[item_id], "score": round(score, 4), "detail": detail[:400]}
    )


def load_report():
    try:
        with open(REPORT_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except Exception as exc:
        return None, str(exc)


def as_int_list(value):
    try:
        return sorted(int(x) for x in value)
    except Exception:
        return None


# ---------------------------------------------------------------- changed_pages
def check_changed_pages(report):
    if report is None:
        add("changed_pages", 0.0, "report missing/unparseable")
        return
    got = report.get("changed_pages")
    lst = as_int_list(got) if isinstance(got, (list, tuple)) else None
    if lst is None:
        # tolerate dict key spellings
        for key in ("changedPages", "changed"):
            if key in report:
                lst = as_int_list(report[key])
                break
    if lst is None:
        add("changed_pages", 0.0, "changed_pages not a list of ints")
        return
    got_set = set(lst)
    false_neg = len(EXPECTED_CHANGED - got_set)
    false_pos = len(got_set - EXPECTED_CHANGED)
    # Asymmetric penalties: failing to detect a real change (e.g. the photo-swap
    # page or the A4 page) is worse than over-reporting noise.
    score = 1.0 - 0.25 * false_neg - 0.15 * false_pos
    detail = f"expected {sorted(EXPECTED_CHANGED)}, got {lst} (missed {false_neg}, extra {false_pos})"
    add("changed_pages", score, detail)


# ----------------------------------------------------- preflight_page_geometry
def check_geometry(report):
    if report is None:
        add("preflight_page_geometry", 0.0, "report missing/unparseable")
        return
    parts, notes = [], []

    fpath = str(report.get("file", ""))
    s = 1.0 if "catalog_v3" in fpath else 0.0
    parts.append(("file field refers to catalog_v3", 0.10, s))

    pc = report.get("page_count")
    try:
        s = 1.0 if int(pc) == EXPECTED_PAGES else 0.0
    except Exception:
        s = 0.0
    parts.append((f"page_count == {EXPECTED_PAGES} (got {pc})", 0.20, s))

    checks = report.get("page_size_check")
    if isinstance(checks, list) and checks:
        ok_hits, dim8, dim1 = 0, None, None
        for entry in checks:
            try:
                pg = int(entry.get("page"))
            except Exception:
                continue
            okval = bool(entry.get("ok"))
            expected_ok = pg != 8
            if 1 <= pg <= 8 and okval == expected_ok:
                ok_hits += 1
            if pg == 8:
                try:
                    w, h = float(entry.get("width_pt")), float(entry.get("height_pt"))
                    if abs(w - A4[0]) <= 1.5 and abs(h - A4[1]) <= 1.5:
                        dim8 = True
                    else:
                        dim8 = False
                except Exception:
                    dim8 = False
            if pg == 1:
                try:
                    w, h = float(entry.get("width_pt")), float(entry.get("height_pt"))
                    dim1 = abs(w - LETTER[0]) <= 1.5 and abs(h - LETTER[1]) <= 1.5
                except Exception:
                    dim1 = False
        parts.append((f"per-page ok flags correct ({ok_hits}/8)", 0.30, ok_hits / 8.0))
        s = 1.0 if dim8 and dim1 else (0.5 if (dim8 or dim1) else 0.0)
        parts.append(("page dims: page8=A4~595.28x841.89, page1=Letter (±1.5pt)", 0.20, s))
    else:
        parts.append(("page_size_check list missing", 0.50, 0.0))

    cnt = report.get("embedded_image_count")
    try:
        s = 1.0 if int(cnt) == EXPECTED_EMBEDDED else 0.0
    except Exception:
        s = 0.0
    parts.append((f"embedded_image_count == {EXPECTED_EMBEDDED} (got {cnt})", 0.20, s))

    total_w = sum(w for _, w, _ in parts)
    score = sum(w * s for _, w, s in parts) / total_w
    detail = "; ".join(t for t, _, _ in parts)
    add("preflight_page_geometry", score, detail)


# ---------------------------------------------------------- undersized_images
def check_undersized(report):
    if report is None:
        add("undersized_images", 0.0, "report missing/unparseable")
        return
    entries = report.get("undersized_images")
    if not isinstance(entries, list):
        add("undersized_images", 0.0, "undersized_images missing/not a list")
        return
    by_page = {}
    for e in entries:
        try:
            by_page[int(e.get("page"))] = e
        except Exception:
            continue

    sub, notes = [], []
    for pg, (w_px, h_px, dpi) in EXPECTED_UNDERSIZED.items():
        e = by_page.get(pg)
        if e is None:
            sub.append(0.0)
            notes.append(f"page {pg} entry missing")
            continue
        sc = 0.3  # page identified
        try:
            got_dpi = float(e.get("effective_dpi"))
            if abs(got_dpi - dpi) <= 2.0:
                sc += 0.5
            else:
                notes.append(f"page {pg} dpi {got_dpi} != {dpi}")
        except Exception:
            notes.append(f"page {pg} dpi unparsable")
        try:
            if int(e.get("width_px")) == w_px and int(e.get("height_px")) == h_px:
                sc += 0.2
        except Exception:
            pass
        sub.append(min(1.0, sc))
    # empty list given but entries exist? handled by page check
    base = sum(sub) / len(sub)
    extras = [p for p in by_page if p not in EXPECTED_UNDERSIZED]
    penalty = 0.15 * len(extras)
    if extras:
        notes.append(f"unexpected extra pages {extras}")
    score = base - penalty
    detail = "; ".join(notes) if notes else "all three undersized images reported correctly"
    add("undersized_images", score, detail)


# ------------------------------------------------------------------- previews
def check_previews(report=None):
    notes, scores = [], []
    for path, (pg1, ew, eh) in EXPECTED_PREVIEWS.items():
        try:
            if not os.path.isfile(path):
                scores.append(0.0)
                notes.append(f"{os.path.basename(path)} missing")
                continue
            from PIL import Image, ImageFilter
            import numpy as np
            with Image.open(path) as im:
                im = im.convert("RGB")
                img = im.copy()
            s = 0.4  # exists & loadable
            w, h = img.size
            if abs(w - ew) <= 2 and abs(h - eh) <= 2:
                s += 0.2
            else:
                notes.append(f"{os.path.basename(path)} dims {w}x{h} != expected {ew}x{eh}")
            # content vs fitz-rendered v3 page (blurred MAE tolerates other rasterizers,
            # but rules out wrong page / rendered from the proof for big changes)
            try:
                import fitz
                doc = fitz.open(V3)
                m = fitz.Matrix(150 / 72, 150 / 72)
                pix = doc[pg1 - 1].get_pixmap(matrix=m, alpha=False)
                ref = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                if ref.size != img.size:
                    ref = ref.resize(img.size)
                a = np.asarray(img.filter(ImageFilter.GaussianBlur(2)).convert("L"), dtype=int)
                b = np.asarray(ref.filter(ImageFilter.GaussianBlur(2)).convert("L"), dtype=int)
                mae = float(abs(a - b).mean())
                if mae <= 0.55:
                    s += 0.4
                else:
                    notes.append(f"{os.path.basename(path)} content mismatch (blurred MAE {mae:.2f})")
            except Exception as exc:
                notes.append(f"{os.path.basename(path)} content check error: {exc}")
            scores.append(s)
        except Exception as exc:
            scores.append(0.0)
            notes.append(f"{os.path.basename(path)} error: {exc}")
    score = sum(scores) / len(scores)
    add("previews", score, "; ".join(notes) if notes else "4 previews present with correct dims and content")


def main():
    report, _err = load_report()
    for fn in (check_changed_pages, check_geometry, check_undersized, check_previews):
        try:
            fn(report)
        except Exception as exc:
            print(f"internal error in {fn.__name__}: {exc}", file=sys.stderr)

    total_w = sum(WEIGHTS[i] for i in RESULT["per_item"])
    det_score = (
        sum(RESULT["per_item"][i] * WEIGHTS[i] for i in RESULT["per_item"]) / total_w
        if total_w else 1.0
    )
    RESULT["score"] = round(det_score, 4)
    print(json.dumps(RESULT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
