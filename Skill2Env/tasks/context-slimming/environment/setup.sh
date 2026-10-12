#!/usr/bin/env bash
# Provision the rollout sandbox for the context-slimming task.
# The base image lacks git; the task requires committing changes inside agent_workspace/.
set -euo pipefail

if ! command -v git >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "git=1:2.39.5-0+deb12u3" \
    || DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git
fi

# Self-check (diagnostic only)
git --version
