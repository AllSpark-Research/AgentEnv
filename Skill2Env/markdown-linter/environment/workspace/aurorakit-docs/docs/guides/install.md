# Installing AuroraKit

AuroraKit runs on Linux, macOS, and Windows (via WSL2).

## Package managers

```bash
npm install -g aurorakit
```

## From source

```bash
git clone https://github.com/aurorakit/aurorakit.git
cd aurorakit
npm install && npm run build
```

Verify the install with `aurorakit --version`; you should see `1.0.0`.

Next step: the [configuration guide](configuration.md).
