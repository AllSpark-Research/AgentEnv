# Storefront Data-Quality Repair Policy (v3)

Applies to: `shop.db` (SQLite), table `products`. The `orders` table is the
audited sales ledger and **must not be modified** in any way.

Repair rules, to be applied in this exact order:

1. **Price normalization.** Every product whose `price_unit` is `cents` must be
   converted to US dollars: `price = price / 100`, rounded to 2 decimals, and
   `price_unit` set to `usd`. Exception: if the SKU also appears in
   `corrections.csv`, DO NOT convert mathematically — the correction file wins
   (rule 2); only flip its `price_unit` to `usd`.
2. **Authoritative corrections.** `corrections.csv` lists retail price
   overrides that are already final **USD** values. Set `price` to the listed
   value for each SKU (and ensure `price_unit` is `usd`). A SKU corrected this
   way is reported under `corrections_applied` only, never under
   `price_normalizations`.
3. **Stock clamps.** Negative `stock` is impossible; clamp it to `0`. Record
   every clamped SKU.
4. **Discontinuations.** Any product whose `name` contains the literal tag
   `[DISCONTINUED]` must be deactivated (`active = 0`). Its price still gets
   normalized by rule 1 if applicable.

Rules 1–4 change ONLY the affected columns of the affected rows. All other
rows, columns, tables, indexes, and constraints stay byte-identical.

After the repair, compute:

- `inventory_value_usd` = sum of `price * stock` over all **active** products
  after all fixes, rounded to 2 decimals.
