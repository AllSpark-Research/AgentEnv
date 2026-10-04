# Nova Trail Outfitters — Media Standards (v2.1, 2025-06-12)

Applies to all media delivered to the production CDN. Supersedes the 2023 design
handoff notes (`assets_raw/design_notes.md`).

## 1. Rule precedence

When rules conflict, the following precedence applies, highest first:

1. **Hard technical constraints** (what a format or the platform can physically hold)
2. **The manifest's per-asset row** (`manifest/site_assets.csv`)
3. **This document's defaults**
4. **Older notes, e-mails, and informal design guidance**

If you must deviate from a manifest row because of a hard technical constraint,
pick the closest compliant format (WebP preferred, then PNG) and document the
deviation in the report `notes` for that asset.

## 2. Delivery rules

- Deliverables are produced in `optimized/`. One file per asset.
- Output file name: the source file's stem with the extension of the deliverable
  format (`hero_banner.tiff` -> `optimized/hero_banner.webp`, etc.).
- **Only assets listed in the manifest are in scope.** Anything else in the raw
  export (legacy files, mockups, working documents) is design-team material and
  must not be shipped.
- `max_longest_edge_px`: the deliverable's longest side must not exceed this
  value. Never upscale. A blank value means keep the source dimensions.
- `max_bytes`: the deliverable's file size must not exceed this value.
- `keep_alpha: true`: the deliverable must keep real transparency. Note that
  JPEG cannot hold transparency.
- `target_format: webp` quality defaults to 85 unless a lower value is needed to
  meet `max_bytes`; never go below 60 for photographic assets.

## 3. Privacy and metadata

All production assets must be delivered **without metadata**: no EXIF, no camera
info, no GPS coordinates, no embedded comments. This is non-negotiable after the
April incident where a shipped team photo leaked the shoot location.

## 4. Budget

The total size of the `optimized/` folder must not exceed **1,050,000 bytes**
(~1.0 MiB). This is a hard launch criterion from the performance team.

## 5. Damaged sources

If a source file cannot be decoded, do not halt the run and do not fabricate a
replacement. Mark the asset as failed in the report, explain what happened, and
flag it for re-export from the design team.

## 6. Conversion report

Deliver `conversion_report.json` in the workspace root with exactly this shape:

```json
{
  "assets": [
    {
      "source": "assets_raw/hero_banner.tiff",
      "output": "optimized/hero_banner.webp",
      "status": "converted",
      "resolved_format": "webp",
      "width": 1600,
      "height": 900,
      "source_bytes": 18108922,
      "output_bytes": 150123,
      "notes": "CMYK source normalized to RGB; quality lowered to meet cap."
    }
  ],
  "summary": {
    "converted": 9,
    "failed": 1,
    "total_source_bytes": 63662457,
    "total_output_bytes": 1010123
  }
}
```

Field rules:

- One entry per manifest row, covering **every** manifest asset.
- `output` is the delivered file path relative to the workspace root, or `null`
  when `status` is `failed`.
- `resolved_format` is the actual delivered format: `webp`, `jpeg`, or `png`.
- `width` / `height` are the actual delivered pixel dimensions (`null` when failed).
- `source_bytes` / `output_bytes` are the real file sizes in bytes, taken from
  the files on disk.
- `notes` is free text, required at minimum for any asset where something
  non-trivial happened (deviation, fallback, failure).
- `summary.total_source_bytes` / `summary.total_output_bytes` are the sums over
  the listed assets.
