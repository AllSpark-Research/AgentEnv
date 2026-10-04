#!/usr/bin/env python3
"""Deterministic verifier for the DAM photo-ingest task.

Rubric items: R1 (deliverable set), R2 (quarantine + source integrity),
R3 (conversion/content fidelity), R4 (metadata), R5 (manifest).
Ground truth is derived from shot_list.csv + pinned authoring-time facts
about incoming_photos/ (the spec's reconciliation rules re-implemented).
"""
import csv
import hashlib
import json
import re
from pathlib import Path

ARTIST = "Riley Alvarez"
COPYRIGHT = "Copyright 2024 Cascade & Pine Outfitters"
COLUMNS = ["shot_id", "product_code", "category", "final_path",
           "source_filename", "actions", "sha256", "quarantined_files"]

# Authoring-time pinned facts about incoming_photos/ (name -> facts)
PINNED = {
 '.DS_Store': {'sha256': '04ec8dedec4ae187da500d78ee035d026c8cbca2488d4d4c59b2f9fcfb4ddafb', 'image': False},
 'DSC0042.JPG': {'sha256': '4e62fe50fcd891c234608e902a23075b250cdbd0e0c2925717f10cef3c2e28e2', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'DSC_0042.JPG': {'sha256': '4e62fe50fcd891c234608e902a23075b250cdbd0e0c2925717f10cef3c2e28e2', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'DSC_0043.JPG': {'sha256': '82dbccae794d384fbec0e3b116fdc7d37581c1c3f03efdb28853a88bd787394c', 'image': True, 'w': 1200, 'h': 900, 'alpha': False},
 'DSC_0043_v2.JPG': {'sha256': '568a01ea5ade70cd90bed0c18b94199ad05e14fa4fbd84ccc30d963c845bd87a', 'image': True, 'w': 2400, 'h': 1800, 'alpha': False},
 'DSC_0045.JPG': {'sha256': '50c109d14188510763687a2d95ae4881ca428b90faf6be3997b961d7864057bc', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG 1023.JPG': {'sha256': '9af95820c55060b3734fc8193768a1fe10f6dd85d8d8b38181b3ba6cff567735', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1001.JPG': {'sha256': '75f8c93cb1e045772e91cc76f229b308ead2e599a992f6d7db0445084ac59233', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1002.JPG': {'sha256': '7ed7eb0fd9622f353b0e72be571239c5783a744abc5e9e9cf1f668b9eaec6f27', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1003.png': {'sha256': '21d614197d36ceb4831e575c82123582d696aa5626b7666fe7c81915aa38d557', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1010.JPG': {'sha256': '22fc2210f82da58378828ce60f7a35eb9c9e8580eaa5d86fdb61b548d680d544', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1011.JPG': {'sha256': '6568be75b34a07c6a68cef41ca06e5b7c7f5589b88a3ef38a393306d3cd1feda', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1012 copy.JPG': {'sha256': 'c01ba49f063889edfe249c647475c5420b38ae8280c065c362fd18a437353873', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1012.JPG': {'sha256': 'c01ba49f063889edfe249c647475c5420b38ae8280c065c362fd18a437353873', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1013.JPG': {'sha256': 'bd36bce28a7cc23c2193dda20d8d5c5a2da2635910d590b3fb3ef57247e039e3', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1020.JPG': {'sha256': 'b43deea9bee79d6baef90bdebcd68a9c1962f8780b95ca0486328632a5fc84fb', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1021.jpg': {'sha256': '8dfcc026e4dc13ca9123368f330a1abc7d903f0d25ef0e175ce66f1d79a20035', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1022.png': {'sha256': 'a0e51985f85b3d1beace30ab5d4d069d523bfca43c62a6137ddb4e2f267fb963', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_1024.JPG': {'sha256': '035b901678e1976c34208d66fcdb51a59c1e6de502867fc1c270e40efea15259', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'IMG_9999.JPG': {'sha256': '0377c5fa47998ace5148d6d7947eb6cf73a75fbda5c508e27814c98527f10124', 'image': True, 'w': 1600, 'h': 1200, 'alpha': False},
 'PXL_patch_logo.png': {'sha256': '42658886cd06747fe32383e89a6a08ddce233b5cec6d8da38d810c92c692919a', 'image': True, 'w': 800, 'h': 800, 'alpha': True},
 'hero_banner_ideas.png': {'sha256': '0cd20823aa8b2d8e4fbf13a0acf27568234d68d0ca71a890e246d2bca6cc673e', 'image': True, 'w': 1200, 'h': 600, 'alpha': True},
 'notes.txt': {'sha256': '4f9837a150fd488df1281497f587ba6e981ad11ba5c6ec29ba8ee28108431632', 'image': False},
 'patch_detail.png': {'sha256': 'fa50542fc00d3a8ab178d826515d6e7d034b5a77efd9e2c64fba6b4a46ab7b75', 'image': True, 'w': 1000, 'h': 1000, 'alpha': True},
}

SHALLOW = (Path(".") / "incoming_photos")


def sha256_file(p: Path):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except Exception:
        return None


def derive_expectations():
    """Apply the spec's rules to pinned facts + shot_list.csv."""
    shots = []
    with open("shot_list.csv", newline="") as f:
        for row in csv.DictReader(f):
            shots.append(row)

    # canonical source per shot (dedup/variant rules on pinned names/hashes)
    canonical, superseded = {}, {}
    for s in shots:
        listed = s["source_filename"]
        stem, ext = Path(listed).stem, Path(listed).suffix
        cands = []
        for name, f in PINNED.items():
            if not f.get("image"):
                continue
            m = re.fullmatch(re.escape(stem) + r"_v(\d+)", Path(name).stem)
            if m and Path(name).suffix.lower() == ext.lower() \
                    and f["sha256"] != PINNED[listed]["sha256"]:
                cands.append(name)
        if cands:
            best = max(cands, key=lambda n: (PINNED[n]["w"] * PINNED[n]["h"], n))
            # sort for determinism: highest pixels, tie -> lexicographically smallest
            best = sorted(cands, key=lambda n: (-PINNED[n]["w"] * PINNED[n]["h"], n))[0]
            canonical[s["shot_id"]] = best
            losers = [n for n in cands if n != best] + [listed]
            superseded[s["shot_id"]] = losers
        else:
            canonical[s["shot_id"]] = listed
            superseded[s["shot_id"]] = []

    used = set(canonical.values())

    dups_of = {}       # shot_id -> [dup basenames]
    duplicates, superseded_files, unlisted, other = [], [], [], []
    listed_names = {s["source_filename"] for s in shots}
    for name, f in PINNED.items():
        if name in used:
            continue
        if not f["image"]:
            other.append(name)
            continue
        dup_shots = [sid for sid, cn in canonical.items() if PINNED[cn]["sha256"] == f["sha256"]]
        if dup_shots:
            duplicates.append(name)
            dups_of.setdefault(sorted(dup_shots)[0], []).append(name)
            continue
        if any(name in v for v in superseded.values()):
            superseded_files.append(name)
            continue
        m = re.fullmatch(r"(.+)_v(\d+)", Path(name).stem)
        if m and any(Path(l).stem == m.group(1) for l in listed_names):
            superseded_files.append(name)  # losing variant not already attributed
            continue
        unlisted.append(name)
    for sid, losers in superseded.items():
        for n in losers:
            if n not in used and n not in superseded_files:
                superseded_files.append(n)

    # expected deliverables + manifest rows
    expected_files, rows, fidelity = {}, [], {}
    for s in shots:
        sid = s["shot_id"]
        cn = canonical[sid]
        cf = PINNED[cn]
        keep_png = cn.lower().endswith(".png") and cf.get("alpha")
        ext = "png" if keep_png else "jpg"
        rel = f"{s['category'].lower()}/{s['product_code'].lower()}_{sid}.{ext}"
        expected_files[sid] = rel
        actions = []
        if cn.lower().endswith(".png") and not keep_png:
            actions.append("CONVERT_PNG_TO_JPG")
            kind = "convert"
        else:
            actions.append("COPY")
            kind = "alpha_png" if keep_png else "copy_jpg"
        if superseded[sid]:
            actions.append("USE_SUPERSEDED_SOURCE")
        q = sorted(dups_of.get(sid, []) + [n for n in superseded.get(sid, []) if n != cn])
        rows.append({"shot_id": sid, "product_code": s["product_code"],
                     "category": s["category"], "final_path": rel,
                     "source_filename": cn, "actions_set": set(actions),
                     "quarantined_set": set(q)})
        fidelity[sid] = {"kind": kind, "source": cn, "w": cf["w"], "h": cf["h"]}
    rows.sort(key=lambda r: r["shot_id"])

    buckets = {"duplicates": sorted(duplicates), "superseded": sorted(superseded_files),
               "unlisted": sorted(unlisted), "other": sorted(other)}
    return shots, expected_files, rows, buckets, fidelity


# ---------------- R1: deliverable set ----------------
def check_R1(expected_files):
    try:
        found, missing = 0, []
        for sid, rel in expected_files.items():
            if (Path("dam_ready") / rel).is_file():
                found += 1
            else:
                missing.append(rel)
        extra = []
        droot = Path("dam_ready")
        if droot.is_dir():
            for p in droot.rglob("*"):
                if p.is_file():
                    relp = str(p.relative_to(droot))
                    if relp != "manifest.csv" and relp not in set(expected_files.values()):
                        extra.append(relp)
        score = max(0.0, (found - len(extra)) / len(expected_files))
        detail = f"{found}/{len(expected_files)} expected deliverables present"
        if missing:
            detail += f"; missing: {missing[:5]}"
        if extra:
            detail += f"; unexpected: {extra[:5]}"
        return score, detail
    except Exception as e:
        return 0.0, f"error: {e}"


# ---------------- R2: quarantine + source integrity ----------------
def check_R2(buckets):
    try:
        bscore, bdet = [], []
        for bucket, names in buckets.items():
            if not names:
                continue
            ok = 0
            for n in names:
                p = Path("quarantine") / bucket / n
                if p.is_file() and sha256_file(p) == PINNED[n]["sha256"]:
                    ok += 1
            bscore.append(ok / len(names))
            bdet.append(f"{bucket}:{ok}/{len(names)}")
        qscore = sum(bscore) / len(bscore) if bscore else 1.0
        total = len(PINNED)
        intact = 0
        for n, f in PINNED.items():
            p = SHALLOW / n
            if p.is_file() and sha256_file(p) == f["sha256"]:
                intact += 1
        extras = []
        if SHALLOW.is_dir():
            for p in SHALLOW.iterdir():
                if p.name not in PINNED:
                    extras.append(p.name)
        iscore = max(0.0, (intact - len(extras)) / total)
        score = 0.5 * qscore + 0.5 * iscore
        detail = ("quarantine " + ",".join(bdet) +
                  f"; incoming intact {intact}/{total}" +
                  (f"; extra in incoming: {extras[:3]}" if extras else ""))
        return score, detail
    except Exception as e:
        return 0.0, f"error: {e}"


# ---------------- R3: fidelity ----------------
def check_R3(expected_files, fidelity):
    try:
        from PIL import Image, ImageChops, ImageStat
    except Exception as e:
        return 0.0, f"PIL unavailable: {e}"
    per = []
    det = []
    for sid, finfo in fidelity.items():
        out = Path("dam_ready") / expected_files[sid]
        src = SHALLOW / finfo["source"]
        if not out.is_file() or not src.is_file():
            per.append(0.0); det.append(f"{sid}:missing"); continue
        try:
            so = Image.open(src); so.load()
            fo = Image.open(out); fo.load()
            kind = finfo["kind"]
            if (fo.width, fo.height) != (finfo["w"], finfo["h"]):
                per.append(0.0); det.append(f"{sid}:wrong-dims"); continue
            if kind == "convert":
                if fo.format != "JPEG" or fo.mode != "RGB":
                    per.append(0.0); det.append(f"{sid}:not-jpeg-rgb"); continue
                diff = ImageChops.difference(so.convert("RGB"), fo.convert("RGB"))
                m = sum(ImageStat.Stat(diff).mean) / 3.0
                per.append(1.0 if m <= 2.0 else (0.5 if m <= 5.0 else 0.0))
                det.append(f"{sid}:conv-diff={m:.2f}")
            elif kind == "alpha_png":
                if fo.format != "PNG":
                    per.append(0.0); det.append(f"{sid}:not-png"); continue
                a = fo.convert("RGBA").getchannel("A")
                if a.getextrema()[0] >= 255:
                    per.append(0.0); det.append(f"{sid}:alpha-lost"); continue
                same = ImageChops.difference(so.convert("RGBA"), fo.convert("RGBA")).getbbox() is None
                per.append(1.0 if same else 0.0)
                det.append(f"{sid}:alpha-exact={same}")
            else:  # copy_jpg
                if fo.format != "JPEG":
                    per.append(0.0); det.append(f"{sid}:not-jpeg"); continue
                diff = ImageChops.difference(so.convert("RGB"), fo.convert("RGB"))
                m = sum(ImageStat.Stat(diff).mean) / 3.0
                # spec forbids recompression: true lossless embedding has diff ~0
                per.append(1.0 if m <= 0.05 else (0.5 if m <= 1.0 else 0.0))
                det.append(f"{sid}:copy-diff={m:.2f}")
        except Exception as e:
            per.append(0.0); det.append(f"{sid}:err")
    return (sum(per) / len(per)), "; ".join(det[:8])


# ---------------- R4: metadata ----------------
def check_R4(expected_files):
    try:
        from PIL import Image
    except Exception as e:
        return 0.0, f"PIL unavailable: {e}"
    good, total, bad = 0, 0, []
    for sid, rel in expected_files.items():
        p = Path("dam_ready") / rel
        if not p.is_file():
            total += 2; bad.append(rel); continue
        try:
            im = Image.open(p)
            if rel.endswith(".png"):
                txt = getattr(im, "text", {}) or {}
                vals = [txt.get("Author"), txt.get("Copyright")]
            else:
                ex = im.getexif()
                vals = [ex.get(315), ex.get(33432)]
            for got, want in zip(vals, [ARTIST, COPYRIGHT]):
                total += 1
                if got == want:
                    good += 1
        except Exception:
            total += 2; bad.append(rel)
    detail = f"{good}/{total} metadata tags correct" + (f"; e.g. {bad[:4]}" if bad else "")
    return good / total, detail


# ---------------- R5: manifest ----------------
def check_R5(rows):
    p = Path("dam_ready") / "manifest.csv"
    if not p.is_file():
        return 0.0, "manifest.csv missing"
    try:
        with open(p, newline="") as f:
            rd = csv.reader(f)
            data = [r for r in rd if r]
        if not data:
            return 0.0, "empty manifest"
        header = [h.strip() for h in data[0]]
        schema_ok = header == COLUMNS
        body = data[1:]
        structure_ok = (len(body) == len(rows) and
                        [r[0].strip() for r in body] == [r["shot_id"] for r in rows])
        base = 0.15 * schema_ok + 0.15 * structure_ok
        row_scores = []
        by_id = {r[0].strip(): r for r in body}
        for exp in rows:
            r = by_id.get(exp["shot_id"])
            if r is None or len(r) < 8:
                row_scores.append(0.0); continue
            s = 0.0
            if r[1].strip() == exp["product_code"]: s += 0.1
            if r[2].strip() == exp["category"]: s += 0.1
            if r[3].strip() == exp["final_path"]: s += 0.1
            if r[4].strip() == exp["source_filename"]: s += 0.1
            if {t.strip() for t in r[5].split(";") if t.strip()} == exp["actions_set"]: s += 0.2
            fp = Path("dam_ready") / r[3].strip()
            if fp.is_file() and r[6].strip().lower() == sha256_file(fp): s += 0.3
            if {t.strip() for t in r[7].split(";") if t.strip()} == exp["quarantined_set"]: s += 0.1
            row_scores.append(s)
        score = base + 0.70 * (sum(row_scores) / len(row_scores))
        detail = (f"schema_ok={schema_ok} structure_ok={structure_ok} "
                  f"row_mean={sum(row_scores)/len(row_scores):.2f}")
        return score, detail
    except Exception as e:
        return 0.0, f"error: {e}"


def main():
    results = {}
    try:
        _, expected_files, rows, buckets, fidelity = derive_expectations()
    except Exception as e:
        for rid in ["R1", "R2", "R3", "R4", "R5"]:
            results[rid] = (0.0, f"expectation derivation failed: {e}")
    else:
        results["R1"] = check_R1(expected_files)
        results["R2"] = check_R2(buckets)
        results["R3"] = check_R3(expected_files, fidelity)
        results["R4"] = check_R4(expected_files)
        results["R5"] = check_R5(rows)

    weights = {"R1": 0.30, "R2": 0.15, "R3": 0.20, "R4": 0.15, "R5": 0.20}
    per_item, checks, total = {}, [], 0.0
    for rid, w in weights.items():
        sc, det = results.get(rid, (0.0, "not run"))
        sc = max(0.0, min(1.0, sc))
        per_item[rid] = sc
        checks.append({"id": rid, "weight": w, "score": sc, "detail": det})
        total += w * sc
    print(json.dumps({"per_item": per_item, "checks": checks, "score": round(total, 4)}))


if __name__ == "__main__":
    main()
