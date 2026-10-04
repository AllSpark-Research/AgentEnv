# Bitterroot Books — incident workspace, 2024-11-14 checkout outage

All log timestamps are UTC. The logs cover the full day of 2024-11-14.

    logs/app/checkout-api.log   JSON structured log, checkout API service
    logs/app/payments.log       JSON structured log, payments service
    logs/nginx/access.log       nginx combined access log
    logs/nginx/error.log        nginx upstream error log
    logs/system/syslog          host syslog (web-01); syslog lines carry no year — they are 2024-11-14
    incident/deploy-history.csv deploys in the 48h around the incident
    incident/tickets.csv        customer support tickets from 2024-11-14
    incident/handoff.md         on-call handoff notes from the responding team
    metrics/disk-usage.csv      hourly disk usage for /var/log on web-01
    runbooks/incident-report-template.md   required postmortem format
