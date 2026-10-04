# INC-2041 follow-up — cleanup approved

**From:** Priya Nair (DBA on call)
**Date:** 2024-08-04
**Ticket:** OPS-1201 (closed)

During the INC-2041 query-latency incident (July) I created two objects
directly in production to diagnose the problem:

- table `temp_dba_scratchpad` — working notes, kept in DB so the whole
  on-call team could see them;
- index `idx_books_price_perf` on `books(list_price)` — a one-off
  experiment to confirm the bad query plan.

Both were created by hand, which is why they never went through the
release branch. The experiment is finished and the notes are copied into
the incident report. **Both objects are approved for removal in v2.3.0.**
If you find any other hand-made objects in the production dump that aren't
in the target schema and aren't covered by a release ticket, flag them in
the diff report instead of dropping silently — but these two are cleared.
