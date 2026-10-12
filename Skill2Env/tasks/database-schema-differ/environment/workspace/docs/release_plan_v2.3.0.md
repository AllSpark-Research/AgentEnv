# Release plan — v2.3.0 (database scope)

Target release schema: `schema/target_v2.3.0.sql` (tagged `v2.3.0-rc1`).
This file is authoritative: after the migration, production must match it.

## 1. Money in cents (DBA-331)

We are standardizing on **integer cents** for all monetary values. The old
columns stored REAL dollars; the new columns are `INTEGER` and named
`*_cents`:

| table        | old column   | new column        |
|--------------|--------------|-------------------|
| books        | list_price   | price_cents       |
| orders       | total        | total_cents       |
| order_items  | unit_price   | unit_price_cents  |

These are the same business values under a new representation — the
application team is not re-pricing anything. Do not lose or reset the data.
Conversion rule: multiply dollars by 100 and round to the nearest cent —
prices are all two-decimal so the result must be exact (watch out for
binary floating point; a naive cast truncates, e.g. 64.99 must become 6499,
not 6498).

# 2. Promotions / discounts (FEAT-210)

- `orders` gains `discount_cents INTEGER NOT NULL DEFAULT 0`.
- Checkout never writes fractional cents.

## 3. Marketing consent flag (CRM-188)

- `customers` gains `marketing_opt_in INTEGER NOT NULL DEFAULT 0`
  (0 = not opted in; existing customers default to 0).

## 4. Reviews & wishlists (FEAT-233, FEAT-240)

Two new tables ship with this release; see the target schema for full DDL:

- `reviews` — 1–5 star ratings (`CHECK (rating BETWEEN 1 AND 5)`) with optional
  text; each review belongs to a book and a customer.
- `wishlists` — one row per customer/book pair (`UNIQUE (customer_id, book_id)`),
  with foreign keys to both tables.
- New supporting indexes: `idx_reviews_book`, and `idx_orders_status`
  (dashboards filter orders by status constantly).

## 5. Data integrity tightening (DBA-340)

`order_items.book_id` is currently unconstrained in production — we have
orphaned line items on record from the cart-service bug in May. This
release adds `FOREIGN KEY (book_id) REFERENCES books(id)`. After the
migration, `PRAGMA foreign_key_check` must return zero violations.

## 6. Retire legacy promo codes (OPS-1188)

`legacy_promo_codes` is superseded by the promotions microservice. The
ops team confirmed the pre-release backup ran (ticket **OPS-1188**); the
table may be dropped in this release.

## 7. Housekeeping

The redundant index `idx_books_isbn` is removed (the `UNIQUE` constraint on
`books.isbn` already enforces uniqueness); target schema reflects this.
