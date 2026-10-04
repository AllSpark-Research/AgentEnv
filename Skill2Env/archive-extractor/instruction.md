You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

You are a data analyst on the operations-analytics team at Ridgeline Distribution. The weekly telemetry handoff from our platform vendor, Talon Telematics, for the operational week 2024-06-17 (Monday) through 2024-06-23 (Sunday) just landed in your workspace.

Reference material in the workspace (read these first):
- README.md - the handoff cover letter: what is inside, coverage expectations, and data-quality notes.
- MANIFEST.csv - the authoritative index of every archive in the handoff: what each file contains and its status (AUTHORITATIVE / SUPERSEDED / DEPRECATED).
- service_targets.csv - the per-site service-level expectations (expected daily uploads, minimum uptime).
- incoming/ - the telemetry archives for the week. Treat this folder as read-only input: you may write extraction output alongside the archives, but do not delete, rename, or alter the archive files themselves.

Your job is the weekly service reconciliation. All five warehouse sites - PIT, CLE, STL, PHX, REN - are expected to have a daily telemetry file for each of the 7 days of the week. Deliver two artifacts:

1) out/handoff_consolidated.csv - the consolidated dataset for the week:
   - Header exactly: site,date,shipments,runtime_min,uptime_pct,source_archive
   - One row per site-day (35 rows total), built only from authoritative system-of-record data - never from stale/backup or deprecated archives.
   - Site codes and ISO dates (YYYY-MM-DD) exactly as in the source files; shipments and runtime_min as integers; uptime_pct numeric - all values exactly as recorded in the telemetry files.
   - source_archive: the archive file each row was recovered from.
   - No duplicate rows.

2) out/weekly_service_report.md - the service report for the ops director. Include, in any order:
   - A short overview of the week and what the handoff covered.
   - Method and sources: which archives you used, which you excluded, and why.
   - A service dashboard table with columns: site | days_received | expected_days | weekly_shipments | avg_uptime_pct | sla_flag - one row per site plus a TOTAL row. Report totals as integers and average uptime rounded to one decimal.
   - SLA assessment: sla_flag is "OK" when the site has all 7 expected days AND avg_uptime_pct >= 95.0, otherwise "FLAG". Apply it per site and explicitly call out any site below target.
   - Findings from the reconciliation and a recommendation on what to do next.

A few uploads in this handoff are known to be problematic - MANIFEST.csv marks them and explains what to do. Verify anything you rely on before consolidating, and make sure the report explains every exclusion. The two deliverables must be internally consistent with each other and with the source telemetry.