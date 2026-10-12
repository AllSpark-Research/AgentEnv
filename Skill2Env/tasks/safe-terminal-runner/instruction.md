You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

The nightly ETL corrupted our storefront catalog and finance needs it reconciled before Monday. The workspace contains `shop.db` (the corrupted SQLite snapshot), `corrections.csv` (authoritative price overrides from merchandising), `policy/data_quality_policy.md` (the repair rules and the order they must be applied in), `notes/handoff.md` (context and housekeeping rules from the previous maintainer), and `.env` (the relevant paths).

Repair the database IN PLACE so it passes every rule in the policy: apply all four rules in the documented order, honoring the documented precedence between the corrections file and the price normalization. The `orders` table is the audited sales ledger and must remain completely untouched.

Then write an audit report for finance to the report path given in `.env`, as a JSON object with exactly these keys:
- `price_normalizations`: {"count": <int>, "skus": [<sorted SKU list>]}
- `stock_clamps`: {"count": <int>, "skus": [<sorted SKU list>]}
- `deactivations`: {"count": <int>, "skus": [<sorted SKU list>]}
- `corrections_applied`: {"count": <int>, "skus": [<sorted SKU list>]}
- `inventory_value_usd`: <number> (post-repair, active products only, 2 decimals)
Every count and SKU list must agree with the actual state of the repaired database.

Finally, follow the housekeeping rules in the handoff note: any one-off scripts you create must use the `temp_` prefix, the repo's `.gitignore` must cover `temp_*`, and no temporary scripts may remain in the workspace when you are done.