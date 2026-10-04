# Brightline Print — Standard Preflight Specification (Saddle-stitch catalogs)

## 1. Trim size

- Required trim: **US Letter, 8.5 × 11 in (612 × 792 pt)**.
- **Every** page must match the required trim size within **±1 pt** in both
  dimensions. A page at any other size (e.g. an A4 export from a design tool)
  is a **blocking failure**.

## 2. Raster image resolution

- Every **raster image** placed in the document must resolve to **at least
  300 effective DPI at its placed size** (i.e. native pixels divided by the
  size it occupies on the page).
- Pure vector artwork is exempt (it has no fixed resolution).
- Any raster image below 300 effective DPI is a **blocking failure** and must
  be reported with its page, native pixel dimensions, and effective DPI
  (report the worst axis when horizontal and vertical differ).

## 3. Client-approval preview renders

When pages have changed relative to an approved proof, send the client one
rendered preview per changed page:

- Rendered from the **release candidate** (the new file), not the proof.
- PNG format, rendered at **150 DPI**.
- One file per changed page, stored in the preview folder, named `page-N.png`
  where **N is the printed (1-based) page number** (e.g. `page-3.png` for the
  third page).

## 4. Numbering conventions

- All page numbers on client-facing artifacts are **1-based printed page
  numbers** (page 1 = the cover). Internal tools that are 0-indexed must be
  translated to printed numbers, never reported raw.
