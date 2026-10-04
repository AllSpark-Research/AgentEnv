# Authentication API

AuroraKit exposes two authentication flows:

- **Dashboard and API clients** authenticate with HTTP bearer tokens. Token
  scopes, lifetimes, and rotation behaviour are described under
  [token lifetimes](./cli-tokens.md).
- **The CLI** authenticates once with a device code and stores a short-lived
  session token, documented in the [CLI token reference](./cli-tokens.md).

Requests without a valid token receive the response codes listed in the
[error code reference](./error-codes.md).
