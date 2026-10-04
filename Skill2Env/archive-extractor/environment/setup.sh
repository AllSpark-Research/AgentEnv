#!/usr/bin/env bash
# Setup for the archive-handoff reconciliation task.
# The skill's .7z backend (py7zr) must be present so STL_week.7z extracts without
# a runtime pip step; py7zr 1.1.3 ships py3.13-compatible wheels.
set -e
pip install --no-input --quiet 'py7zr==1.1.3' || pip install --no-input 'py7zr==1.1.3'
# self-check (diagnostic; not a hard failure)
python3 -c "import py7zr; print('py7zr ok:', py7zr.__version__ if hasattr(py7zr,'__version__') else '1.1.3')"
pip freeze | grep -i py7zr || echo "py7zr not shown in freeze (preinstalled at image build) — okay"