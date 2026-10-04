# Architecture overview

AuroraKit has three moving parts: the collector agent, the stream processor,
and the dashboard server.

![system diagram](../images/architecture.png)

The collector agent samples each datasource every 30 seconds and pushes
batches to the stream processor over gRPC. The stream processor maintains a
five-minute tumbling window per metric, and the dashboard server subscribes
to the topics it renders. Operational procedures live in the
[operations runbook](../ops/runbook.md).
