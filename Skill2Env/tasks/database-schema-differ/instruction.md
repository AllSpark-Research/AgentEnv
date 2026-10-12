You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

We're cutting release v2.3.0 of our Lumen Books storefront backend and you're preparing the database release artifacts for the DBA review board.

The repo root you're in has everything you need: the latest production schema dump (schema/prod_2024-08-01.sql, captured from the live DB), the authoritative target schema for this release (schema/target_v2.3.0.sql), a sampled production data extract for testing (data/prod_extract_2024-08-01.sql), the release plan and change policy under docs/, ops follow-ups under ops/, and a vendored schema-diff CLI under _skill_ref/ (usage in _skill_ref/SKILL.md).

Reconcile the actual production schema with the target release schema using all of those sources, and produce three things:

1. migrations/V2_3_0__release.sql — the single forward migration for this release. It must run as-is against our SQLite databases: when applied to a database created from schema/prod_2024-08-01.sql plus data/prod_extract_2024-08-01.sql, it must leave the database in exactly the target schema — same tables, columns (including types, defaults, and constraints), primary keys, foreign keys, and indexes, nothing extra and nothing missing. All business data on retained objects must survive (same rows, same primary keys), and every monetary value must be converted from REAL dollars to integer cents exactly (multiply by 100, round to the nearest cent — all current values are two-decimal so this must come out exact; beware naive float casts). Handle the money-column renames as renames-with-conversion, not drop-and-add. Validate the migration yourself against the extract before shipping it.

2. reports/schema_diff_report.md — the change report for the review board. Enumerate every schema difference between the production dump and the target schema, grouped by change type, state how each one is handled in the migration (e.g. rename+convert vs. add vs. drop), and call out the risks a reviewer should care about (data conversion, referential integrity, destructive changes and their authorizing tickets). It must account for every difference, including objects that exist only in production — the release plan deliberately doesn't cover everything in the dump.

3. ci/check_schema_drift.sh — the CI drift gate, runnable from the repo root. It takes one argument (a path to a .sql schema file describing the actual state of a database), compares it against the expected release schema, exits 0 when there is no drift and non-zero when drift is detected.

Don't ask me follow-ups — the docs and dumps answer everything; if the production dump contains things the release plan doesn't mention, resolve them from the ops notes.