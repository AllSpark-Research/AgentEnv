You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

Meridian Analytics security review (STD-SEC-217) is blocking our next release until every GitHub Actions workflow in this repo snapshot uses OIDC federation for cloud access. I need you to do the whole remediation pass.

The repo's authoritative rules are in `security/identity-standard.md`, the approved action pins are in `security/action-pins.yml` (don't modify anything under `security/` or `docs/`), and the OIDC identities platform engineering provisioned are in `docs/oidc-identity-map.md`. Live workflows are under `.github/workflows/`. The exports under `archived/` are historical records - out of scope, do not touch them.

Do the following, in order:

1. Before changing any workflow, run the OIDC hardening audit over the live workflows and save its JSON output to `audit/before.json` as the baseline (use the auditor's default thresholds).
2. Go through EVERY live workflow - not just the ones the audit report highlights - and bring it into compliance with the standard. Fix the workflows in place. Each fix must use the exact identities and pins from the two security docs above.
3. When everything is remediated, re-run the same audit and save the JSON output to `audit/after.json`. The release gate requires zero flagged workflows.
4. Write `REMEDIATION_REPORT.md` at the repo root for the security reviewers. It should summarize the compliance gaps found per workflow, what you changed and why, any risky patterns the audit tooling itself under-reported or missed entirely, the repo secrets that can now be decommissioned, and the verification evidence (baseline vs final audit results).

Keep each workflow's existing behavior intact (triggers, build/deploy/export commands, environments) - only the authentication and permission posture should change.