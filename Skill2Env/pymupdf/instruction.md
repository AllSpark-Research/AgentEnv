You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

I run preflight at a print shop and just took in a rush job (see docs/intake_email.md for the full story and file roles — please read it and docs/print_spec.md first).

The client sent their final catalog PDF and the last proof they approved, both in incoming/, and claims only a few small edits went in after approval. I don't trust that claim, and I need the approval package before we can burn plates.

Do the following and place everything under deliverables/:

1. Work out exactly which pages of the final catalog actually changed visually compared to the approved proof — changed content of any kind counts, including swapped artwork or altered page geometry.

2. Preflight the final catalog against our standard spec in docs/print_spec.md (trim size on every page, and minimum placed raster resolution).

3. Write deliverables/preflight_report.json with exactly this structure (all page numbers are 1-based printed page numbers):
   {
     "file": "<path of the final catalog you checked>",
     "page_count": <int>,
     "page_size_check": [{"page": <int>, "width_pt": <float>, "height_pt": <float>, "ok": <bool>}, ...one entry per page...],
     "embedded_image_count": <int, unique raster images embedded in the final catalog>,
     "undersized_images": [{"page": <int>, "width_px": <int>, "height_px": <int>, "effective_dpi": <float, worst axis at placed size>}, ...],
     "changed_pages": [<int>, ...]
   }
   undersized_images lists every raster image below the spec minimum, empty list if none; changed_pages must be complete and sorted.

4. Render the client-approval previews for the changed pages into deliverables/previews/, following the naming and resolution conventions in the spec.

5. Write deliverables/review_notes.md — a short note for the client's account manager summarizing what actually changed between the proof and the final, every spec failure that blocks plating (with page numbers and the numbers behind each failure), and what they need to fix or approve before we proceed. Keep it factual and free of anything you can't back up from the files.

Round effective DPI to one decimal. Don't disturb anything in incoming/ or docs/.