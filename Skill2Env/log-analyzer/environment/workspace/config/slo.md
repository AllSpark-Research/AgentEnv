# OrderDesk SLOs

## Checkout success SLO
- Target: **99.5%** of checkout attempts succeed, measured over a rolling 28-day window.
- A checkout attempt (POST /checkout) counts as failed if it returns a 5xx response.
- Paging alert: success rate < 99.5% over a rolling 10-minute window, sustained for
  two consecutive 5-minute evaluations (this dampens short bursts and means pages can
  lag the onset of a real incident by several minutes).
- Error budget: 0.5% of attempts per 28 days.

## Notes
- Transient provider timeouts that recover on an automatic retry do NOT count against
  the customer-facing SLO as long as the customer request ultimately succeeds.
- Known non-SLO defects tracked separately in the bug tracker (e.g. the longstanding
  `gift_wrap_code` finalize bug that sporadically 500s single orders).
