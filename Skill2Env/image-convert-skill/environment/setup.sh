#!/bin/bash
# Idempotent environment provisioning for the media-optimization task.
# Pillow is required by the skill script (scripts/convert.py) and by the verifier.
set -e
python3 -c "import PIL" 2>/dev/null || true
pip install --no-input --quiet "Pillow==12.3.0"
# self-check (diagnostic)
python3 -c "import PIL; print('Pillow OK:', PIL.__version__)"
