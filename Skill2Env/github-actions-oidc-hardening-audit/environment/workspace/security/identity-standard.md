# Cloud Identity Standard — GitHub Actions (STD-SEC-217)

Effective 2024-09-01. Applies to every workflow that runs in this repository
(`.github/workflows/`). Archived exports under `archived/` are out of scope.

## 1. OIDC federation only

All authentication to AWS, GCP, and Azure from GitHub Actions **must** use OIDC
federation. Long-lived cloud credentials are forbidden in workflows, including:

- AWS access keys (`aws-access-key-id` / `aws-secret-access-key` inputs or
  `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` secrets)
- GCP service-account key JSON (`credentials_json` inputs, key files written at
  runtime, `gcloud auth activate-service-account --key-file=...`)
- Azure client secrets / publish-profile JSON (`creds:` inputs,
  `AZURE_CREDENTIALS` / `AZURE_CLIENT_SECRET` secrets)

These apply **regardless of which step or tool consumes the credential** — direct
CLI usage of a static cloud key is just as non-compliant as passing one to an
official auth action.

## 2. Approved authentication pattern

Use the official auth action for each cloud, pinned to a full 40-character commit
SHA from `security/action-pins.yml`:

| Cloud | Action           | OIDC inputs                                                  |
|-------|------------------|--------------------------------------------------------------|
| AWS   | `aws-actions/configure-aws-credentials` | `role-to-assume`, `aws-region`           |
| GCP   | `google-github-actions/auth`            | `workload_identity_provider`, `service_account` |
| Azure | `azure/login`                            | `client-id`, `tenant-id`, `subscription-id`          |

Role ARNs, workload identity providers, service accounts, and Azure IDs for each
environment are maintained in `docs/oidc-identity-map.md`. Do not invent values.

## 3. Token permissions — job-level scoping required

Every job that performs cloud authentication **must** declare
`permissions: id-token: write` in the **job's own** `permissions` block, together
with any other permissions the job needs (usually `contents: read`).

Declaring `id-token: write` only at the top (workflow) level does **not** satisfy
this requirement: when a job defines its own `permissions` block, the workflow-level
permissions are not merged in, and the OIDC token request will fail at runtime.

`permissions: write-all` is forbidden.

## 4. Action pinning

Cloud auth actions must be pinned to the full commit SHA listed in
`security/action-pins.yml`, with the human-readable version kept as a trailing
comment (e.g. `uses: aws-actions/configure-aws-credentials@<sha> # v4`).
Branch refs (`@main`) and major-version tags (`@v4`) are not acceptable for auth
actions.

## 5. Decommissioning static secrets

When a workflow is migrated to OIDC, the repo secrets it used
(`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `GCP_SERVICE_ACCOUNT_KEY`,
`AZURE_CREDENTIALS`, …) must be reported for deletion so security can remove them.
