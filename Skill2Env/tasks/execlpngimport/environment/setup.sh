#!/usr/bin/env bash
# Task needs nothing beyond the base image (openpyxl 3.1.5 already installed).
# Excel-only skill path; no cnocr/OCR required.
set -e
pip freeze | grep -i '^openpyxl==' || echo "WARN: openpyxl not found"
# none
