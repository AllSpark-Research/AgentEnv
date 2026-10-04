# Target Schema — `clean/orders_clean.csv`

Authoritative rules for the Q2 2024 order-feed warehouse load. Produce exactly
these columns, in this order:

| Column | Type / rule |
| --- | --- |
| `order_id` | `ORD-` followed by 4 digits. Unique in the output after dedupe (see `operations_note.md`). |
| `order_date` | ISO 8601 date `YYYY-MM-DD`. |
| `customer_name` | Free text. Optional. Trim whitespace; empty if missing. |
| `customer_email` | Required. Lowercased, trimmed, and matching `^[^@\s]+@[^@\s]+\.[^@\s]+$`. |
| `sku` | Required. Must exist in `docs/product_catalog.csv`. |
| `quantity` | Required. Integer, minimum 1. |
| `unit_price_usd` | Required. Decimal with exactly two fractional digits. Convert EUR/GBP using `docs/fx_rates.json` (round half-up to cents). |
| `status` | Required. One of `paid`, `pending`, `refunded`, `cancelled` (lowercase). |
| `region` | One of `US`, `EU`, `UK`, as exported. |

## Normalization rules

- Null tokens (case-insensitive) `""`, `-`, `N/A`, `null`, `NONE` mean "missing".
  A missing value in a required field makes the row a reject. A missing value in
  the one optional field (`customer_name`) becomes an empty string.
- Trim surrounding whitespace on every field before validating.
- Status values are case-insensitive and may carry stray spaces; canonicalize
  to the lowercase domain above.
- Currency is indicated in the raw `Unit Price` text (see
  `operations_note.md`). Bare numbers with no symbol are USD.
- Sort `orders_clean.csv` by `order_id` ascending, one header row, UTF-8.

## Rejects — `clean/rejects.csv`

Any raw row that fails a required-field rule above (after null token and
whitespace normalization) must NOT go into `orders_clean.csv`. Send it to
`clean/rejects.csv` with exactly these columns, in this order:

- `source_row` — the row's 1-based position among data rows in
  `data/orders_export.csv` (the header is not counted).
- `order_id` — the raw order id (if present), so support can trace it.
- `reason` — short human-readable explanation of why the row was rejected.

Keep one rejects row per rejected source row.
