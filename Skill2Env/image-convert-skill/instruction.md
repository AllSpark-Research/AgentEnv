You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

I'm finishing the media library for the Nova Trail Outfitters site relaunch. The design team's raw export is in `assets_raw/` and it's in rough shape: huge CMYK TIFFs, BMP exports, a camera-upload JPEG, one export the design team already warned might be damaged, plus some legacy working material they kept in the folder.

The per-asset delivery requirements are in `manifest/site_assets.csv`, and our media standards are in `policy/media_standards.md` — including the audit report format we must hand to the platform team and a hard size budget for the delivered folder.

Please produce, in the workspace root:

1. `optimized/` — the web-ready successor file for every deliverable asset, following the naming, dimension, dimension-cap, format, and byte-cap rules, and honoring the metadata/privacy rules in the standards.
2. `conversion_report.json` — the audit report in exactly the format the standards describe, covering every asset listed in the manifest, including any asset that could not be produced.

Anything in the raw export that isn't part of the delivery set must not be shipped. Where a stated requirement contradicts what an image format can actually hold, follow the precedence the standards define and document your resolution in the report. Verify what you ship rather than trusting that the raw export behaved.