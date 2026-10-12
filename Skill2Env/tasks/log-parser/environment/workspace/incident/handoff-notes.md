# Incident handoff — Luminabasket (luminabasket.example)

**From:** R. Okafor (outgoing on-call)
**To:** next on-call (you)
**Written:** 2024-11-18 16:20 UTC

Rough night. PagerDuty fired at **13:41 UTC** ("web 5xx rate" + "login
latency p99" alerts). I didn't have time to finish the triage — you do.

What I know so far:

- Elevated 5xx on the web tier and a big flood of traffic hammering
  **/api/login** this evening. Security thinks **credential stuffing**
  (stack of:
    login attempts = POST against /api/login
    rejected = HTTP 401 (invalid credentials)
    blocked by rate limiter = HTTP 403 (counted separately, below)
    ```
  `/api/login` successes outside the attack pool are essentially impossible:
  real users authenticated via OAuth this quarter.
- **blocked_rate_limit_hits**: number of `/api/login` requests (any method, any
  source) that were rejected with **403** by the rate limiter.
- **auth_log_anomalies**: count of `/api/login` request lines whose **query
  string contains credentials in cleartext** (i.e. path starts with
  `/api/login?`) — we need to know how badly the API leaks passwords into
  access logs.
- **dist_event_sources**: the union of distinct source IPs that produced
  either a 401 login attempt (web) or an sshd "Failed password" line (bastion),
  counted once each.
- **correlated_attack_ips**: list of IPs that appear in the web access log AND
  in the bastion auth failures.
- All timestamps UTC ISO-8601. The findings record is consumed by a job that
  diffs it against the CMDB, so keep the field names exactly as below.
