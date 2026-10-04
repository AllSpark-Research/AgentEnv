# Luminabasket — Security Incident Triage Report

**Incident date (UTC):** _TODO_
**Author:** _TODO (on-call triage)_
**Audience:** security lead; attach to the PagerDuty incident record.

Complete every numbered section below and remove the _TODO_ placeholders.
All times must be UTC. Keep internal hostnames/IPs accurate; the report is
also read by engineering. `report/findings.json` and this report must agree.

## 1. Executive summary

_TODO — 3-6 sentences: what happened, when (UTC), what was affected, worst
impact, current state._

## 2. Timeline (UTC)

_TODO — ordered UTC timeline correlating the three log sources (web tier,
bastion, api-service). Include at minimum: first malicious web request, first
bastion ssh failure from the attacker, onset of the 5xx wave, first breached
account, last malicious web request._

## 3. Findings by system

### 3.1 Web tier (`logs/web-access.log`)

_TODO_

### 3.2 Bastion host (`logs/bastion-auth.log`)

_TODO_

### 3.3 API service (`logs/api-service.log`)

_TODO_

## 4. Impact

_TODO — quantified: requests, rejected logins, breached accounts, error wave._

## 5. Root cause

_TODO_

## 6. Recommended actions

_TODO — concrete, owner-ready actions (technical controls first)._
