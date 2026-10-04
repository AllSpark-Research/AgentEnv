# HTTP bearer tokens

Bearer tokens authenticate requests to the AuroraKit HTTP API.

## Lifetimes

| Scope       | Default lifetime | Renewable |
| ----------- | ---------------- | --------- |
| `read`      | 24 h             | yes       |
| `write`     | 4 h              | yes       |
| `publish`   | 90 days          | no        |

Rotate publish tokens with `aurorakit tokens rotate`.

## Header format

```
Authorization: Bearer ak_live_...
```

See the [authentication overview](./authentication.md) for how these tokens
relate to CLI sessions.
