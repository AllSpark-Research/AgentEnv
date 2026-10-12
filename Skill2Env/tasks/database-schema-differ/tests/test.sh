#!/usr/bin/env bash
set -euo pipefail
cd /app
exec python3 /tests/run_verifier.py
