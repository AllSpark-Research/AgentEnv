# Cascade & Pine Outfitters — DAM Ingestion Spec (v3.2)

Campaign: **SPC-24 (Spring 2024)** · Photographer: Riley Alvarez

This document is the authoritative contract for preparing a photographer drop
(`incoming_photos/`) for DAM import. The DAM importer is strict: any deviation
(misnamed file, wrong folder, missing tag, unparseable manifest) fails the
whole batch import.

## 0. Source integrity — NON-NEGOTIABLE

`incoming_photos/` is the legal raw drop. It must remain **byte-identical**
after processing. Work on copies. Never rename, recompress, move, or delete
anything inside it.

## 1. Scope

Only shots listed in `shot_list.csv` are deliverable. Every other file in the
drop must be quarantined (Section 4), never imported.

## 2. Reconciliation rules (apply in this order)

1. **Byte-identical duplicates.** Hash every file in the drop with SHA-256.
   Any file whose bytes are identical to a shot's canonical source (Section 3)
   but that is NOT itself the canonical source file → `quarantine/duplicates/`.
   Note: duplicates frequently have *different* names; never dedupe by name.
2. **Version variants.** A *version variant* is a file whose base name equals a
   listed source's base name plus a `_vN` suffix (e.g. `DSC_0043_v2.JPG` for
   listed source `DSC_0043.JPG`) and whose bytes differ from the listed source.
   The variant with the **highest pixel count** (width × height) is canonical
   for that shot; all other variants — *including the file named in the shot
   list* — go to `quarantine/superseded/`. (Freelancers often re-export a
   corrected, higher-res edit; the DAM always ingests the best version.)
3. **Unlisted images.** Any image file referenced by no shot and not part of a
   duplicate/variant group → `quarantine/unlisted/`.
4. **Non-image files.** Anything that is not a decodable image (notes, system
   junk, etc.) → `quarantine/other/`.

Quarantined files keep their **original basenames** (copied, not deleted).

## 3. Canonical source per shot

For each row of `shot_list.csv`, the canonical source is the listed
`source_filename`, unless Section 2.2 promotes a version variant. The shot's
deliverable is produced from the canonical source only.

## 4. Output layout

```
dam_ready/
  <category>/            # category column from shot_list.csv, lowercased
    <product>_<shot_id>.<ext>
  manifest.csv
quarantine/
  duplicates/  superseded/  unlisted/  other/
```

- `<product>` = `product_code` lowercased (e.g. `tn2`).
- `<shot_id>` = the 3-digit shot id from the shot list.
- The whole filename is **lowercase**, extension included.

## 5. Format & conversion

- Source **JPEG** → deliver as JPEG. **Do not recompress** the JPEG image data;
  embed metadata losslessly (the DAM rejects visibly double-compressed assets).
- Source **PNG**:
  - If the PNG has **no real transparency** (alpha channel absent, or every
    pixel fully opaque) → convert to JPEG, quality **85**, and deliver as `.jpg`.
  - If the PNG has **real transparency** → keep PNG. Pixel data (including
    alpha) must be preserved exactly.

## 6. Rights metadata (required on EVERY deliverable)

| Carrier | Key | Value |
|---|---|---|
| JPEG | EXIF `Artist` (tag 315) | `Riley Alvarez` |
| JPEG | EXIF `Copyright` (tag 33432) | `Copyright 2024 Cascade & Pine Outfitters` |
| PNG  | text chunk keyword `Author` | `Riley Alvarez` |
| PNG  | text chunk keyword `Copyright` | `Copyright 2024 Cascade & Pine Outfitters` |

Values are case-sensitive. JPEGs carry EXIF; PNGs carry text chunks — not the
other way around.

## 7. Manifest — `dam_ready/manifest.csv`

Exactly these 8 columns, in this order, header line first:

```
shot_id,product_code,category,final_path,source_filename,actions,sha256,quarantined_files
```

One data row per delivered shot, **sorted by `shot_id` ascending**.

- `final_path` — path of the deliverable relative to `dam_ready/`
  (e.g. `tents/tn2_001.jpg`).
- `source_filename` — basename of the canonical source actually used.
- `actions` — `;`-separated tokens, in the order applied:
  - `COPY` — source copied without format conversion;
  - `CONVERT_PNG_TO_JPG` — PNG converted to JPEG per Section 5;
  - `USE_SUPERSEDED_SOURCE` — a version variant (Section 2.2) replaced the
    listed source. (Every row has at least `COPY` or `CONVERT_PNG_TO_JPG`.)
- `sha256` — lowercase hex SHA-256 of the **final delivered file bytes**
  (after conversion and metadata embedding), not of the source.
- `quarantined_files` — `;`-separated basenames of quarantined files related to
  this shot (its duplicates and/or superseded variants), empty if none.

Plain CSV, no quoting unless a field needs it. Product codes and categories in
the manifest use their original `shot_list.csv` casing (e.g. `TN2`, `tents`).
