You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

You are helping the on-call team at Bitterroot Books, a small online bookseller. On 2024-11-14 (all times UTC) the checkout flow was effectively down for roughly 90 minutes and the team needs the follow-up analysis finished.

The workspace contains everything that was collected: per-service logs under logs/, the last 48h of deploys in incident/deploy-history.csv, that day's support tickets in incident/tickets.csv, on-call handoff notes in incident/handoff.md, host disk metrics in metrics/disk-usage.csv, and the required postmortem format in runbooks/incident-report-template.md.

Produce two deliverables at the workspace root:

1. incident_report.md — the postmortem, following runbooks/incident-report-template.md. It must quantify user impact (failed 5xx responses from the nginx access log with the affected time window, and the customer ticket volume), lay out a UTC timeline, and present one defensible root cause backed by the evidence — including explicitly addressing any hypothesis in the handoff notes that the evidence does not support — plus concrete corrective and preventive action items.

2. incident_digest.json — a machine-readable error digest of the two application service logs (logs/app/checkout-api.log and logs/app/payments.log) covering the whole of 2024-11-14, at WARN severity and above, with the chronic DATA-882 slow-query warnings excluded (they are a known, unrelated issue). Operations will import this JSON into the status dashboard.

Note that these are historical logs from 2024-11-14; make sure any time filtering you apply actually covers that day.
