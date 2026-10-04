#!/usr/bin/env bash
# Environment provisioning for the task sandbox.
# Base image is a python:3.13 image (no C compiler by default).
set -u

# 1) C toolchain needed to build pyppmd (a py7zr dependency) which ships no cp313 wheel.
if ! command -v gcc >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gcc >/dev/null
fi

# 2) 7z support for the file-sorter skill (plain and encrypted .7z archives).
python3 -c "import py7zr" 2>/dev/null || pip install --no-input "py7zr==0.22.0"

# Self-check (diagnostic; non-fatal)
python3 -c "import py7zr; print('py7zr OK:', py7zr.__version__)" || echo "WARNING: py7zr unavailable"
gcc --version | head -1 || echo "WARNING: gcc unavailable"
