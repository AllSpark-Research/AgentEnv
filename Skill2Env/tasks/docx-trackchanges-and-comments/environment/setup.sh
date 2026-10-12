#!/bin/bash
# Environment provisioning for the MSA redline task.
# Base image already provides: python3.13, python-docx 1.2.0, lxml, unzip.
# The `zip` CLI is NOT installable in this image; repacking uses Python zipfile,
# so no extra packages are required. This script only self-checks.
set -e

python3 -c "import docx, lxml; print('python-docx OK:', docx.__version__ if hasattr(docx, '__version__') else 'installed')"
command -v unzip >/dev/null && echo "unzip OK"
python3 -c "import zipfile; print('zipfile OK')"
# none
