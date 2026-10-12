# Database change policy (excerpt — release engineering)

1. **Migration format.** Each release ships exactly one forward migration
   script under `migrations/`. It must be production-ready SQL that runs
   against our SQLite databases as-is with any standard SQLite driver.
   Generated scaffolds and skeletons are a starting point only — anything
   committed must be complete, reviewed SQL, with no placeholders.

2. **Data preservation.** A migration may not lose business data on any
   retained object: row counts and primary keys must survive. Renames and
   representation changes move the data, they do not discard it. Objects
   may only be dropped when a ticket in the release plan or an ops
   follow-up explicitly authorizes it — cite the ticket in a comment in
   the migration and in the diff report.

3. **Exactness of money.** All monetary values are integer cents after
   v2.3.0. Conversion at migration time must be exact for the two-decimal
   dollar values we hold: no float truncation drift, no rounding errors.

4. **Validation before handoff.** The release engineer validates the
   migration against the sampled production extract in `data/` before the
   DBA review: row counts on retained tables, referential integrity
   (`PRAGMA foreign_key_check`), and spot-checked converted values.

5. **CI drift gate.** Every release must leave `ci/check_schema_drift.sh`
   working. The gate takes one argument — a path to a `.sql` schema file
   describing the *actual* state of a database — and compares it against
   the expected release schema using the repo's vendored schema-diff CLI
   (`_skill_ref/scripts/main.py`, see its `check-drift` command). It exits
   `0` when there is no drift and non-zero when drift is detected
   (`--fail-on-drift`). CI invokes it from the repo root.

6. **Diff report.** `reports/` must contain a report for the DBA review
   board enumerating every schema difference between the production dump
   and the target schema, grouped by change type, with the handling
   decision for each item (e.g. rename vs. add/drop) and the associated
   risks. The report is part of the release: reviewers reject releases
   whose report does not account for every observed difference, including
   objects that exist only in production.
