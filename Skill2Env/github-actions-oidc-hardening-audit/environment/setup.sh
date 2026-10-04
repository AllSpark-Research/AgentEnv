#!/usr/bin/env bash
# Environment provisioning for the OIDC hardening remediation task.
# The base image already provides bash + python3 with PyYAML (verified: 6.0.3),
# which is all the skill script and the verifier need. Nothing extra to install.
set -euo pipefail
python3 -c "import yaml; print('pyyaml:', yaml.__version__)" || pip install --no-input PyYAML==6.0.3
bash --version | head -1
