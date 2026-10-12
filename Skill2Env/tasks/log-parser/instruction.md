You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

You're the incoming on-call for Luminabasket (e-commerce). The previous on-call was paged last night about a web 5xx spike and a flood of traffic on the login endpoint, suspected credential stuffing, and left a partial handoff in incident/handoff-notes.md. Platform logging conventions are documented in infra/logging-standards.md; the raw logs from the three affected systems are in logs/ (web tier access log, bastion sshd log, api-service event log). Pull the incident apart and file the post-incident record:

1. report/findings.json — copy report/findings.template.json to this path, replace every placeholder, and delete the _comment/_definition helper keys. Every metric definition in the template is normative: count exactly what the definition says. All timestamps must be UTC ISO-8601.
2. report/incident-report.md — complete every numbered section of the existing skeleton (executive summary, UTC timeline correlating all three log sources, findings per system, impact, root cause, recommended actions). It goes to the security lead and is attached to the incident record; findings.json and the report must agree.

Notes: don't trust raw request volume alone when deciding who the attacker is — check what each top talker is actually doing. Mind the timezones of the different log sources (see the infra doc). Some local analysis tooling exists in this environment; verify its actual behavior rather than assuming its docs are accurate.