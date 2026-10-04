#!/usr/bin/env python3
"""Deterministic verifier for the MSA redline task.

Run from the solver's final workspace root:  python3 verify.py
Prints exactly one JSON line with per-item scores and exits 0.
"""
import json
import re
import zipfile
from xml.etree import ElementTree as ET

DOCX = "Vendor_MSA_v3_redline.docx"

WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
RTNS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# (label, deleted string, inserted string, required live context around the edit)
EDITS = [
    ("payment terms", "Net 45", "Net 30", "due and payable Net 30 from"),
    ("renewal notice window", "thirty (30) days", "sixty (60) days", "at least sixty (60) days before the end"),
    ("liability cap", "$25,000", "$102,000", "not exceed $102,000"),
    ("governing law", "State of New York", "State of Delaware", "governed by the laws of the State of Delaware"),
]

PRESERVED = [
    "$8,500 per month",
    "99.5%",
    "Exhibit A",
    "MASTER SERVICES AGREEMENT",
    "INDEMNIFICATION",
    "gross negligence or willful",
    "All undisputed invoices are due and payable",
    "before the end of the then-current term",
    "aggregate liability arising out of or relating to this Agreement",
    "without regard to its conflict-of-laws principles",
]

UNTOUCHED = "seventy-two (72) hours"


def norm(s):
    return re.sub(r"\s+", " ", s or "")


def localname(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def collect_revisions_and_live(root):
    """Walk document.xml; return (deleted_text, inserted_text, live_text, revisions, markers)."""
    deleted, inserted, live = [], [], []
    revisions = []  # (kind, author)
    markers = {"commentRangeStart": [], "commentRangeEnd": [], "commentReference": []}

    def walk(el, in_del, in_ins):
        ln = localname(el.tag)
        if ln == "del":
            in_del = True
            revisions.append(("del", el.get("{%s}author" % WNS)))
        elif ln == "ins":
            in_ins = True
            revisions.append(("ins", el.get("{%s}author" % WNS)))
        if ln in ("commentRangeStart", "commentRangeEnd", "commentReference"):
            markers[ln].append(el.get("{%s}id" % WNS))
        if ln in ("t", "delText") and el.text:
            if in_del:
                deleted.append(el.text)
            else:
                live.append(el.text)
                if in_ins:
                    inserted.append(el.text)
        for child in el:
            walk(child, in_del, in_ins)

    walk(root, False, False)
    return " ".join(deleted), " ".join(inserted), " ".join(live), revisions, markers


def load_part(zf, name):
    try:
        return zf.read(name)
    except Exception:
        return None


def check_tracked_edits():
    """D1: the four required edits exist as real revisions and the live text reflects them."""
    detail = []
    try:
        zf = zipfile.ZipFile(DOCX)
        root = ET.fromstring(zf.read("word/document.xml"))
    except Exception as e:
        return 0.0, "cannot open/parse output docx: %s" % e
    deleted, inserted, live, revisions, _ = collect_revisions_and_live(root)
    d, i, l = norm(deleted), norm(inserted), norm(live)
    frac = 0.0
    for label, old, new, ctx in EDITS:
        c = 0
        conds = [
            (old in d, "del '%s'" % old),
            (new in i, "ins '%s'" % new),
            (new in l, "live '%s'" % new),
            (old not in l, "live excludes '%s'" % old),
            (ctx in l, "clause context intact ('%s')" % ctx),
        ]
        for ok, msg in conds:
            if ok:
                c += 1
            else:
                detail.append("%s: FAIL %s" % (label, msg))
        frac += c / 5.0 / len(EDITS)
    if not revisions:
        detail.append("no w:ins/w:del revision elements found at all")
    detail.append("revisions found: %d" % len(revisions))
    return round(frac, 4), "; ".join(detail)[:400] or "all four edits correct"


def check_revision_state():
    """D2: trackChanges on, authors = Priya Raman, breach clause NOT revised."""
    parts = []
    detail = []
    try:
        zf = zipfile.ZipFile(DOCX)
        settings_raw = load_part(zf, "word/settings.xml")
        root = ET.fromstring(zf.read("word/document.xml"))
    except Exception as e:
        return 0.0, "cannot open/parse output docx: %s" % e

    ok = False
    try:
        ok = settings_raw is not None and ET.fromstring(settings_raw).find(".//{%s}trackChanges" % WNS) is not None
    except Exception:
        ok = False
    parts.append(0.4 if ok else 0.0)
    if not ok:
        detail.append("w:trackChanges missing from settings.xml")

    deleted, inserted, live, revisions, _ = collect_revisions_and_live(root)
    if revisions:
        good = sum(1 for _, a in revisions if a and "raman" in a.lower())
        parts.append(0.3 * good / len(revisions))
        if good != len(revisions):
            detail.append("%d/%d revision elements not authored 'Priya Raman'" % (len(revisions) - good, len(revisions)))
    else:
        parts.append(0.0)
        detail.append("no revisions to attribute")

    l = norm(live)
    d = norm(deleted)
    untouched_ok = UNTOUCHED in l and "seventy-two" not in d
    parts.append(0.3 if untouched_ok else 0.0)
    if not untouched_ok:
        detail.append("section 7.2 breach-notice wording was improperly revised or lost")

    return round(sum(parts), 4), "; ".join(detail)[:400] or "trackChanges on, authors OK, sec 7.2 untouched"


def check_comment_infra():
    """D3: comments part declared, related, populated, and id-consistent."""
    detail = []
    try:
        zf = zipfile.ZipFile(DOCX)
        names = zf.namelist()
    except Exception as e:
        return 0.0, "cannot open output docx: %s" % e
    score = 0.0

    comments_raw = load_part(zf, "word/comments.xml")
    comment_ids, authors_ok = [], 0
    if comments_raw is None:
        detail.append("word/comments.xml missing")
    else:
        try:
            croot = ET.fromstring(comments_raw)
            score += 0.15
            for c in croot.iter("{%s}comment" % WNS):
                cid = c.get("{%s}id" % WNS)
                comment_ids.append(cid)
                a = c.get("{%s}author" % WNS) or ""
                if "raman" in a.lower():
                    authors_ok += 1
            if len(comment_ids) >= 3 and len(set(comment_ids)) == len(comment_ids) and None not in comment_ids:
                if authors_ok == len(comment_ids):
                    score += 0.20
                else:
                    score += 0.20 * authors_ok / len(comment_ids)
                    detail.append("some comments not authored 'Priya Raman'")
            else:
                detail.append("need >=3 comments with unique ids; found %d" % len(comment_ids))
        except Exception as e:
            detail.append("comments.xml unparseable: %s" % e)

    try:
        ct = zf.read("[Content_Types].xml").decode("utf-8", "replace")
        if "/word/comments.xml" in ct and "comments+xml" in ct:
            score += 0.20
        else:
            detail.append("no Override for /word/comments.xml in [Content_Types].xml")
    except Exception as e:
        detail.append("cannot read [Content_Types].xml: %s" % e)

    try:
        rels = ET.fromstring(zf.read("word/_rels/document.xml.rels"))
        found = False
        for rel in rels:
            t = rel.get("Type", "")
            if t.endswith("/comments"):
                found = True
        if found:
            score += 0.20
        else:
            detail.append("no comments relationship in document.xml.rels")
    except Exception as e:
        detail.append("cannot parse document.xml.rels: %s" % e)

    try:
        root = ET.fromstring(zf.read("word/document.xml"))
        _, _, _, _, markers = collect_revisions_and_live(root)
        starts, ends, refs = set(markers["commentRangeStart"]), set(markers["commentRangeEnd"]), set(markers["commentReference"])
        cids = set(comment_ids)
        if comment_ids and starts == ends == refs == cids:
            score += 0.25
        else:
            detail.append(
                "id mismatch: comments=%s rangeStart=%s rangeEnd=%s reference=%s"
                % (sorted(x for x in cids if x), sorted(x for x in starts if x),
                   sorted(x for x in ends if x), sorted(x for x in refs if x))
            )
    except Exception as e:
        detail.append("cannot check document.xml markers: %s" % e)

    return round(score, 4), "; ".join(detail)[:400] or "comment infrastructure complete and consistent"


def check_comment_substance():
    """D4: comments actually ask about 48h timeline, mutuality, and 99.9% uptime."""
    detail = []
    try:
        zf = zipfile.ZipFile(DOCX)
        croot = ET.fromstring(zf.read("word/comments.xml"))
    except Exception as e:
        return 0.0, "cannot open/parse comments.xml: %s" % e
    texts = []
    for c in croot.iter("{%s}comment" % WNS):
        texts.append(" ".join(t.text or "" for t in c.iter() if localname(t.tag) in ("t", "delText")))
    agg = " ".join(texts).lower()
    score = 0.0
    for needle, label in [(r"\b48\b", "48-hour timeline"), (r"mutual", "mutual confidentiality"), (r"99\.9", "99.9% uptime")]:
        if re.search(needle, agg):
            score += 1.0 / 3.0
        else:
            detail.append("no comment mentions %s" % label)
    return round(score, 4), "; ".join(detail)[:400] or "all three comment topics present"


def check_preservation():
    """D5: doc still valid and non-target language preserved."""
    detail = []
    try:
        zf = zipfile.ZipFile(DOCX)
        bad = zf.testzip()
        if bad:
            return 0.0, "corrupt zip member: %s" % bad
    except Exception as e:
        return 0.0, "cannot open output docx: %s" % e
    score = 0.0
    try:
        from docx import Document
        doc = Document(DOCX)
        n_par = len(doc.paragraphs)
        if n_par >= 20:
            score += 0.3
        else:
            detail.append("suspicious paragraph count: %d" % n_par)
    except Exception as e:
        detail.append("python-docx cannot open: %s" % e)
    try:
        root = ET.fromstring(zf.read("word/document.xml"))
        _, _, live, _, _ = collect_revisions_and_live(root)
        l = norm(live)
        missing = [s for s in PRESERVED if s not in l]
        score += 0.5 * (len(PRESERVED) - len(missing)) / len(PRESERVED)
        if missing:
            detail.append("lost non-target text: %s" % missing)
    except Exception as e:
        detail.append("cannot verify preserved text: %s" % e)
    try:
        ct = zf.read("[Content_Types].xml").decode("utf-8", "replace")
        if "wordprocessingml.document.main+xml" in ct:
            score += 0.2
        else:
            detail.append("main document content-type override missing")
    except Exception as e:
        detail.append("cannot read [Content_Types].xml: %s" % e)
    return round(score, 4), "; ".join(detail)[:400] or "document valid, non-target text preserved"


ITEMS = [
    ("tracked_edits", 0.35, check_tracked_edits),
    ("revision_state", 0.12, check_revision_state),
    ("comment_infra", 0.15, check_comment_infra),
    ("comment_substance", 0.08, check_comment_substance),
    ("preservation", 0.10, check_preservation),
]


def main():
    per_item, checks = {}, []
    for rid, weight, fn in ITEMS:
        try:
            score, detail = fn()
        except Exception as e:
            score, detail = 0.0, "verifier error in %s: %s" % (rid, e)
        score = max(0.0, min(1.0, score))
        per_item[rid] = score
        checks.append({"id": rid, "weight": weight, "score": score, "detail": detail})
    total_w = sum(wgt for _, wgt, _ in ITEMS)
    overall = sum(per_item[rid] * wgt for rid, wgt, _ in ITEMS) / total_w if total_w else 0.0
    print(json.dumps({"per_item": per_item, "checks": checks, "score": round(overall, 4)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"per_item": {}, "checks": [{"id": "error", "weight": 1.0, "score": 0.0, "detail": str(e)}], "score": 0.0}))
    raise SystemExit(0)
