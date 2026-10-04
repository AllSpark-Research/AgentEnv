# Q2 2024 Order Feed — Warehouse Load Prep

We received the quarterly order export from the ShopFlow storefront (all three
regional tenants merged into one file) and need it cleaned to our warehouse
schema before the load on Friday.

## What's here

- `data/orders_export.csv` — the raw merged export from ShopFlow (US, EU, and UK
  tenants). Headers, dates, prices, and statuses are *not* consistent across
  regions. Do not modify this file in place; treat it as read-only source data.
- `docs/target_schema.md` — the authoritative target schema and validation
  rules for the warehouse load (`clean/orders_clean.csv`) and the rejects file.
- `docs/operations_note.md` — notes from Priya (ShopFlow ops) about regional
  export conventions and how re-exports/duplicates should be handled.
- `docs/product_catalog.csv` — current product catalog (valid SKUs).
- `docs/fx_rates.json` — finance-approved FX snapshot for this load.

## Known context

- The export covers orders placed between 2024-03-01 and 2024-04-30.
- ShopFlow re-exports an order's full row whenever its state changes, so the
  file contains re-export duplicates.
- Finance requires all money in the warehouse to be USD with exactly two
  decimal places.
