You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

I'm getting the drawing review package ready for tomorrow's bid review meeting (Riverside Community Center). The CAD exports we received from the architect are in `cad_exports/`, and their cover transmittal is in `transmittal.md` — it explains which revision of the site plan is current and has notes on some of the other files.

Please put together the package:

1. **Previews** — Render a PNG preview of every drawing in the *current* review set into `previews/`, roughly 1200 pixels wide, one file per drawing named after its source (e.g. `previews/site_plan_R3a.png`). Superseded site-plan revisions don't need previews. Verify that each preview actually shows the drawing before you ship it — a couple of these exports are known to be problematic, so don't trust a clean exit code alone.

2. **Web export** — Export an SVG of the current site plan for the web team as `web/site_plan.svg`.

3. **QA manifest** — Write `manifest.json` at the workspace root with a top-level `files` array containing one object per file in `cad_exports/`, each with these fields:
   - `file`: path to the source file relative to the workspace (e.g. `cad_exports/site_plan_R3a.dxf`)
   - `status`: one of `ok` (rendered cleanly), `recovered` (needed repair before it could be used), `failed` (could not be rendered), or `superseded` (replaced by a newer revision)
   - `entity_count`: total number of graphical entities across model space AND paper space layouts; `null` for failed files
   - `layers`: sorted list of layers that actually contain entities; `null` for failed files
   - `extents`: `{min_x, min_y, max_x, max_y}` bounding box of all entities in drawing units; `null` for failed files
   - `preview`: relative path to its preview PNG, or `null` if it has none
   - `notes`: free text (may be an empty string)

4. **QA note** — Write a short `qa_report.md` for the project manager: which files gave you trouble, what was actually wrong with each, and how you dealt with them (or why a file can't be included this round).

A DXF conversion skill is available in the environment if you want it; use whatever tooling gets the job done correctly.