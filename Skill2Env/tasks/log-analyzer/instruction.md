You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

You are the on-call SRE lead for OrderDesk, Northwind Supply Co.'s e-commerce platform. Today (all times UTC) monitoring paged you for incident INC-2781 ("CheckoutSuccessRateLow" — checkout success rate below the 99.5% rolling 10-minute threshold) at 2025-04-18T14:12:03Z, and customer support has filed tickets about failed checkouts.

The workspace contains everything available: README.md (orientation), incident/pager_alert.json, incident/customer_tickets.md, incident/deploys.log, the service logs under logs/ (api-gateway.log, checkout-service.log, payment-worker.log, fraud-detector.log; formats differ per service), runbooks/incident_report_template.md (required postmortem structure), and config/slo.md (SLO and alerting definitions).

Produce the postmortem pack as three deliverables (paths relative to the workspace root):

1. analysis/summary.json — machine-readable incident facts with EXACTLY this schema:
{
  "incident_id": "INC-2781",
  "incident_start_utc": "<ISO-8601 UTC timestamp of the first failing payment event of the incident>",
  "incident_end_utc": "<ISO-8601 UTC timestamp of the last failing payment event of the incident>",
  "recovery_utc": "<ISO-8601 UTC timestamp of the first successful payment capture after the incident>",
  "total_payment_failure_events": <integer: count of individual payment-attempt failure events during the incident, counting every retry attempt of every order>,
  "distinct_failed_orders": <integer: number of distinct orders that permanently failed (were dead-lettered) during the incident>,
  "distinct_failed_requests": <integer: number of distinct checkout requests that permanently failed during the incident>,
  "gateway_checkout_5xx_count": <integer: number of 502 responses to POST /checkout in the gateway log over the whole log span>,
  "checkout_success_rate_pct_during_window": <number: percentage (0-100) of distinct orders with any payment attempt during the incident window that had at least one successful capture>,
  "root_cause_signature": "<short text identifying the provider-level error responsible>",
  "t1042_request": {"request_id": "...", "order_id": "...", "failed_stage": "<service/stage where this request ultimately failed>"}
}
Notes: the alert does NOT mark the incident start — determine the true window from the logs. Carefully separate permanently failed orders from retry attempts and from unrelated pre-existing background errors; ticket T-1042 in customer_tickets.md names a specific customer request — locate it across the services and confirm where it failed.

2. analysis/timeline.csv — a merged, chronologically ordered record of the key events relevant to the incident gathered across ALL sources (deploys, alert, service logs, support tickets). Header line exactly: timestamp,service,event,details. Use ISO-8601 UTC timestamps in the first column. Include at minimum: the trigger deploy, the incident start (first failure), the alert firing, the rollback deploy, and the recovery (first successful payment after the fix).

3. incident_report.md — the postmortem for INC-2781, following the section structure of runbooks/incident_report_template.md, for an engineering audience. It must state the true incident window with concrete log evidence; quantify customer impact; explain the root cause as a chain (distinguishing the trigger from the underlying cause and explicitly ruling out the other plausible explanations present in the material); describe how the incident was detected, including any gap between onset and detection; and list concrete action items.

Work directly from the workspace material; all deliverables must be consistent with each other and with the logs.