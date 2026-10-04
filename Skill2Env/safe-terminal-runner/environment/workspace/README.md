# Storefront Reconciliation Workspace

Contents:

- `shop.db` — SQLite snapshot of the storefront catalog (`products`) and sales
  ledger (`orders`). Currently fails the data-quality checks in
  `policy/data_quality_policy.md`.
- `corrections.csv` — authoritative retail price overrides from the
  merchandising team (final USD prices).
- `policy/data_quality_policy.md` — the repair rules and their order of
  application.
- `notes/handoff.md` — context and housekeeping rules from the previous
  maintainer.
- `.env` — paths for the database and the audit report.
