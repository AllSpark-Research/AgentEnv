# CLI tokens

The AuroraKit CLI exchanges a device code for a short-lived session token.

```bash
aurorakit login
# opens the device-authorization page, prints a code like WXYZ-1234
```

Session tokens expire after 12 hours and are stored in the per-user config
directory. They cannot be used as HTTP bearer tokens; the HTTP API only
accepts the bearer tokens described in [auth-tokens](./auth-tokens.md).
