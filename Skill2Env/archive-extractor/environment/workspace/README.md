# Talon Telematics - Weekly Platform Handoff

**Operational week: 2024-06-17 (Mon) through 2024-06-23 (Sun)**
Prepared by the Talon Telematics platform operations team for Ridgeline Distribution ops-analytics.
Generated: 2024-06-24 06:15 UTC.

## What is in this handoff

| Path | Purpose |
|------|---------|
| `MANIFEST.csv` | **Authoritative index** of every archive in this handoff - read it first. It lists each file, what it contains, and its status (AUTHORITATIVE / SUPERSEDED / DEPRECATED). |
| `service_targets.csv` | Service-level expectations per site (expected daily uploads, minimum uptime). Use this for the weekly SLA assessment. |
| `incoming/` | The telemetry archives themselves. Extraction output may be written alongside the archives in this folder. Do **not** delete, rename, or re-upload any of the source archives - treat `incoming/` as read-only input. |

## Coverage this week

All five warehouse sites (PIT, CLE, STL, PHX, REN) are expected to have uploaded one daily
telemetry file per day for every day of the operational week (7 days each). A site that missed
uploads or reported degraded uptime should appear in the weekly service review.

## A note on data quality

A small number of uploads in this handoff are known to be problematic. `MANIFEST.csv` marks the
files in question and what to do with them. Please base the weekly consolidation only on data you
can verify as the platform's system of record, and call out in your report anything you excluded
and why.

Platform support (handle: `#tier2-telemetry`) is available if you need a re-export; no re-export
was requested for this week.
