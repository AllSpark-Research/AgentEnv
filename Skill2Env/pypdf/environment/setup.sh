#!/usr/bin/env bash
# Environment for the audit-packet task: the pypdf skill and the verifier need pypdf.
set -euo pipefail

pip install --no-input pypdf==6.14.2

# self-check (diagnostic)
pip freeze | grep -i '^pypdf==' || true
