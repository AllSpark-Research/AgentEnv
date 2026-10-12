# Configuring AuroraKit

AuroraKit reads `aurorakit.config.yaml` from the working directory.

```yaml
server:
  port: 8787
datasources:
  - name: prometheus
    url: http://localhost:9090
```

Every supported key, its type, and its default are listed in the
[configuration schema][schema]. Unknown keys are rejected at startup.

[schema]: ./config-schema.md
