# Troubleshooting

This page absorbed the old FAQ.

## The dashboard shows "source unreachable"

Check that the datasource URL is reachable from the machine running
`aurorakit serve`. Corporate proxies are the most common culprit.

## AuroraKit exits with a numeric status

Consult the [error code reference](../reference/error-codes.md) for the exact
meaning of every exit status and HTTP response code emitted by the server.

## Still stuck?

Escalate through the [operations runbook](../ops/runbook.md).
