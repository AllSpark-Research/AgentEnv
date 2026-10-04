# Notes from ShopFlow Ops (Priya) — export conventions

Hey! Some context on the merged export you got from us:

## Dates and times

- The **US tenant** exports slash dates as **MM/DD/YYYY** and 12-hour clock
  times (e.g. `06/20/2024 2:05 PM`).
- The **EU and UK tenants** export slash dates as **DD/MM/YYYY** with 24-hour
  times (e.g. `16/06/2024 14:05`).
- You'll also see ISO 8601 (`2024-03-07`, `2024-06-17T15:26:00Z`) and textual
  dates (`12-Apr-2024`) — those are unambiguous.
- The `Region` column tells you which tenant the row came from, so you can
  resolve slash dates correctly. If a slash date can't be resolved or isn't a
  real calendar date, treat the row as bad data.

## Money

- US rows are USD (`$` prefix or a bare number). EU rows are EUR and use the
  continental format: `.` thousands separator, `,` decimal separator — so
  `€1.299,00` means one thousand two hundred ninety-nine euros. UK rows are
  GBP (`£`).
- Convert to USD for the load with the finance snapshot in
  `docs/fx_rates.json` — please use those exact rates, not live market rates.

## Re-exports / duplicates

Our storefront re-exports an order's full row every time its state changes, so
` Order ID ` can appear more than once. For the warehouse load, keep the record
with the **most recent `UPDATED_AT`** for each order id and drop the stale
copies. The dropped copies should be listed in your cleanup notes so nothing
disappears silently.

## Encoding

The file is UTF-8 with a BOM, comma-separated, CRLF line endings.

— Priya
