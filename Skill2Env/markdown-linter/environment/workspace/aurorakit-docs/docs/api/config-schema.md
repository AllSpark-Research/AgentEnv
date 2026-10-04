# Configuration schema

Version: `config.aurorakit.dev/v1`

| Key                  | Type    | Default            |
| -------------------- | ------- | ------------------ |
| `server.port`        | integer | 8787               |
| `server.host`        | string  | `127.0.0.1`        |
| `datasources[].name` | string  | (required)         |
| `datasources[].url`  | string  | (required)         |
| `tokens.publish_ttl` | string  | `90d`              |

The schema is validated on startup; see [troubleshooting](../guides/troubleshooting.md)
for common misconfigurations.
