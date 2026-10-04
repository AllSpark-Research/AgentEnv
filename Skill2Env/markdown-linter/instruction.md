You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

I'm preparing the AuroraKit 1.0.1 documentation refresh and our release gate currently fails on documentation link integrity.

The docs repo sits in `aurorakit-docs/`. In March we restructured the whole tree (PR #612); the authoritative record of what moved is `aurorakit-docs/docs/migration/moves-1.0.md`, and the support team distilled recent user complaints in `aurorakit-docs/reports/triage-notes.md`.

Your job:

1. Find and repair EVERY internal link in `aurorakit-docs/` that is broken or lands readers on the wrong page. Fix links in place — point them at the current, correct target according to the migration map and the triage notes. Do NOT create stub files at old locations to make links resolve, do NOT delete problematic links, and do NOT modify or move any file that has no link defect in it.
2. A markdown link-linter tool is available in this workspace (a directory with an `index.js` you can run via node). Run it to establish the audit baseline BEFORE you change anything, and re-run it after your fixes to confirm the tree is clean.
3. Write a human-readable audit report at `aurorakit-docs/link-audit.md`: the baseline scan results and how you obtained them, every fix you made (file, old target, new target, and why), and — this matters to us — an honest account of what the automated linter does NOT catch and how you made sure nothing slipped through.
4. Write a machine-readable manifest at `aurorakit-docs/link-audit.json` for our CI gate, with exactly this shape:

```json
{
  "baseline": {"files_scanned": <int>, "broken_links_found": <int>},
  "additional_broken_references": <int>,
  "fixes": [{"file": "...", "from": "...", "to": "..."}]
}
```

`baseline` must be the pristine run of the linter, before your edits. `fixes` lists every defective reference you repaired, one entry each, with `file` relative to `aurorakit-docs/` and `from`/`to` being the link targets as written in the markdown before and after your change. `additional_broken_references` counts the defective references you found that the linter's baseline report did not flag.

A linter-clean tree is necessary but not sufficient — our gate also verifies every link lands where readers expect it to.