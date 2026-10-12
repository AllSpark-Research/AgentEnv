# On-call handoff notes — 2024-11-14 (all times UTC)

From Maya (primary on-call):

- Customers started complaining about checkout failures right after 14:00.
- The checkout-api log is full of connection/pool errors from ~14:03 until things
  settled down around 15:35.
- I rolled checkout-api back to v2.13.2 at 15:22 and new checkouts went green again.
  See deploy-history.csv.

From Taylor (secondary):

- I still think the disk filled up — I saw `disk-check` WARNING lines about
  /var/log in syslog at 14:00 and 15:00, right when it broke. Maya disagrees.
- NOTE: the `slow query ... (DATA-882)` warnings in checkout-api.log are the chronic
  sessions-cleanup query we've had since October. Priya confirmed they are NOT
  related to this incident — treat them as known noise, exclude them from any digest.

From Priya (eng manager):

- We need a postmortem: `incident_report.md` following runbooks/incident-report-template.md.
- Operations also needs a machine-readable error digest of the two app services
  (checkout-api and payments) for the whole of 2024-11-14 as JSON for the status
  dashboard — save it as `incident_digest.json`. WARN severity and above is fine.
  Please keep the DATA-882 slow-query noise out of it.
- Quantify user impact: failed (5xx) responses from the nginx access log, and the
  customer ticket volume in incident/tickets.csv.
- Corroborate or rule out the disk theory with metrics/disk-usage.csv.
