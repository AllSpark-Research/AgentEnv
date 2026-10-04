#!/bin/sh
# No additional dependencies: the task needs only node + python3 from the base image.
# Diagnostic self-checks (non-fatal):
node --version 2>/dev/null || echo "WARN: node not found"
python3 --version 2>/dev/null || echo "WARN: python3 not found"
