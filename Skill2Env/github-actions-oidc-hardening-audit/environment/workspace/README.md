# meridian-platform (workspace snapshot)

Infrastructure workflows for Meridian Analytics.

- Live GitHub Actions workflows live in `.github/workflows/`.
- `security/` contains the cloud identity standard and the approved action-pin registry
  that all workflow cloud-authentication changes must follow.
- `docs/oidc-identity-map.md` lists the OIDC roles / workload-identity resources that
  platform engineering provisioned for each cloud environment.
- `archived/` contains historical exports kept for reference only. Nothing under
  `archived/` is deployed or maintained; do not modify it.

Only files under `.github/workflows/` run in CI. Treat everything in there as production
configuration.
