#!/bin/sh
# Environment provisioning for the INC-2781 postmortem task.
# The log-analyzer skill's JSON-log workflows assume `jq`; the base image lacks it.
set -e
if ! command -v jq >/dev/null 2>&1; then
  apt-get update -y >/dev/null 2>&1 || true
  apt-get install -y jq >/dev/null 2>&1 || true
fi
command -v jq && jq --version
command -v python3 && python3 --version
