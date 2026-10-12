You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

We're onboarding the Q2 2024 ShopFlow order feed into our warehouse, and the merged export we received (`data/orders_export.csv`, covering the US, EU, and UK tenants) is too messy to load as-is. Please get it load-ready.

Specifically, I need four deliverables:

1. `clean/orders_clean.csv` — the cleaned order data conforming to `docs/target_schema.md` (that file is authoritative for columns, formats, validation, and sorting).
2. `clean/rejects.csv` — the raw rows that cannot meet the schema rules, in the format `docs/target_schema.md` defines, so support can follow up.
3. `reports/profile_report.md` — a profile of the raw export covering what you actually found: its structure, the data quality issues present (with counts), and a short quality scorecard. Only report what the data supports — no invented metrics.
4. `reports/cleanup_plan.md` — the reproducible, step-by-step cleanup plan that produced the two CSVs, so a colleague could re-run it or audit it. Document every irreversible decision (dropped rows, conversions) and any assumptions you made.

The raw export is read-only source data — don't modify it. `docs/operations_note.md` has context from the vendor on regional conventions and re-exports; use it together with `docs/product_catalog.csv` and `docs/fx_rates.json` (finance wants those exact rates, not market rates).