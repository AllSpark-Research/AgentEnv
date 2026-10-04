# Lumen Books — storefront backend

Small e-commerce backend for the Lumen Books storefront. Data layer is a
single SQLite database; releases are stamped out by the *release prep*
process described below.

## Repository layout

```
schema/    Schema dumps (production snapshots, target release schema)
data/      Sampled production data extracts for migration testing
docs/      Release plan and database change policy
ops/       Incident / ops follow-ups that affect the database
migrations/ Release migration scripts (one per release)
reports/   Release review artifacts (diff reports, sign-offs)
ci/        CI gate scripts
_skill_ref/ Vendored schema-diff CLI (see _skill_ref/SKILL.md); run its
            commands as `python3 _skill_ref/scripts/main.py <command>`
```

## Release prep, in one paragraph

Before every release we: reconcile the last production schema dump with the
release branch's target schema, write one migration script under
`migrations/`, produce a schema-diff report for the DBA review board under
`reports/`, and make sure the CI drift gate under `ci/` is green. The hard
rules live in `docs/db_change_policy.md`; the scope of a given release lives
in its plan under `docs/`.

Quick local check when preparing a migration:

```bash
python3 _skill_ref/scripts/main.py compare schema/prod_2024-08-01.sql schema/target_v2.3.0.sql
```
