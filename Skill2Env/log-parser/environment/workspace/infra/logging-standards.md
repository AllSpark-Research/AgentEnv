# Luminabasket platform — logging standards (excerpt)

_Applies to: production fleet, current as of 2024-09._

## Time and timezones

- All hosts keep their clocks on **local time UTC+8** (site ops requirement).
- **The api-service is the one exception**: its JSON event log is emitted by
  the container platform and timestamps are always **UTC ISO-8601** ("Z").
- The web tier (nginx) writes access logs in the local timezone, e.g.
  `18/Nov/2024:21:09:11 +0800`.
- syslog (incl. sshd on the bastion) writes the traditional `Nov 18 21:09:11`
  format — **no year, no timezone**; it is host-local time.
- Anything we hand to HQ (reports, findings records, tickets) must be
  expressed in **UTC**. Convert before you file.

## Networks and special hosts

- Infra RFC1918 range: **10.20.0.0/16** (VPC). Anything from this range in the
  access log is internal traffic.
- **10.20.0.15** = monitoring host "mon-01". It scrapes `/healthz` on the web
  tier every 30 s around the clock. Benign by definition; exclude it from
  security analysis (it will dominate any naive "top talker" view — you have
  been warned).
- Egress NAT for staff VPN: 203.0.113.10 (corp). Deploys come from there.

## File locations handed over for this incident

- `logs/web-access.log` — nginx access log, web tier (rotated 2024-11-19 00:00
  local; single day of traffic).
- `logs/bastion-auth.log` — sshd events from bastion-01 (syslog format).
- `logs/api-service.log` — api-service JSON events (UTC).

## Known tooling quirks

- The internal `log_parser.py` helper is a work in progress; its README and
  its actual CLI flags have drifted apart. If a documented flag is rejected,
  run it with `--help` or read the source before assuming the file is broken.
