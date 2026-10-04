# OrderDesk — incident workspace (INC-2781)

OrderDesk is Northwind Supply Co.'s e-commerce platform. Relevant service topology:

```
client → api-gateway → checkout-service → fraud-detector
                                   └──→ payment-worker (charge execution, provider: PayVault)
```

On 2025-04-18 monitoring paged the on-call SRE for incident **INC-2781** (checkout failures).
This directory collects the material available for the postmortem:

- `incident/pager_alert.json` — the monitoring alert that paged on-call
- `incident/customer_tickets.md` — support tickets filed during the failure (customer-facing times are approximate)
- `incident/deploys.log` — deploy/config-change log for the platform
- `logs/` — service logs covering 2025-04-18, 12:00–16:30 UTC:
  - `api-gateway.log` — edge access log (nginx-style; includes `request_id` token and `rt` response time)
  - `checkout-service.log` — structured JSON lines
  - `payment-worker.log` — plain text with embedded Python tracebacks
  - `fraud-detector.log` — structured JSON lines
- `runbooks/incident_report_template.md` — required postmortem structure
- `config/slo.md` — SLO definitions for the checkout flow

All timestamps are UTC. Cross-service tracing uses the `request_id` / `requestId` /
`request=` field (also visible to customers as an error-page reference) and, within a
customer's order, the `order` / `orderId` field.
