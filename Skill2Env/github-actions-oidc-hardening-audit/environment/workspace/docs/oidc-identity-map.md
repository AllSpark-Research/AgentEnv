# OIDC Identity Map (authoritative)

Provisioned 2024-08-12 by platform engineering (ticket PLAT-3391). These are the
**only** OIDC identities approved for use from GitHub Actions in this repository.
Match each workflow to an environment by the cloud resources it already targets
(project IDs, buckets, subscriptions named in the workflow and its commands).

## AWS

| Environment       | Account ID   | Role ARN                                                       |
|-------------------|--------------|----------------------------------------------------------------|
| `aws-staging`     | 111122223333 | `arn:aws:iam::111122223333:role/github-actions-staging-deploy` |
| `aws-prod`        | 444455556666 | `arn:aws:iam::444455556666:role/github-actions-prod-deploy`    |
| `aws-prod-backup` | 444455556666 | `arn:aws:iam::444455556666:role/github-actions-prod-backup`    |
| `aws-sandbox`     | 777788889999 | `arn:aws:iam::777788889999:role/github-actions-sandbox`        |

`aws-sandbox` is for local experimentation only; no repository workflow uses it.

## GCP

Service-account key JSON is deprecated everywhere; use Workload Identity Federation.

| Environment     | Project / number                  | Workload identity provider                                                                 | Service account |
|-----------------|-----------------------------------|--------------------------------------------------------------------------------------------|-----------------|
| `gcp-ml-prod`   | `meridian-ml-prod` / 583920174655   | `projects/583920174655/locations/global/workloadIdentityPools/github-actions/providers/github` | `github-ml-training@meridian-ml-prod.iam.gserviceaccount.com` |
| `gcp-data-prod` | `meridian-data-prod` / 910284756312 | `projects/910284756312/locations/global/workloadIdentityPools/github-actions/providers/github` | `github-data-export@meridian-data-prod.iam.gserviceaccount.com` |

## Azure

| Environment  | Client ID                              | Tenant ID                              | Subscription ID                          |
|--------------|----------------------------------------|----------------------------------------|------------------------------------------|
| `azure-prod` | `05032e4e-d1be-427c-8483-877103465e47` | `c32cca8c-8436-425f-8ea8-685e3adb1549` | `1d8ceee9-324b-4f9e-baaf-f72fefc6fdf5` |

The Azure federated credential is scoped to this repository's `azure-prod` deployment.
