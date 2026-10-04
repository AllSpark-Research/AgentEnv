# Error codes

Every numeric status AuroraKit can emit, grouped by layer.

| Code  | Layer | Meaning                        |
| ----- | ----- | ------------------------------ |
| 1001  | CLI   | config file unreadable         |
| 1002  | CLI   | datasource unreachable         |
| 2401  | HTTP  | missing or expired token       |
| 2403  | HTTP  | token scope insufficient       |
| 2504  | HTTP  | datasource timeout             |

Token-related codes assume you have read the
[authentication overview](./authentication.md).
