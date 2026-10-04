#!/usr/bin/env bash
# Environment provisioning for the DAM photo-ingest task.
# Base image already provides python3 + Pillow; add piexif for lossless
# JPEG EXIF embedding (the ingestion spec forbids JPEG recompression).
set -euo pipefail

python3 -c "import piexif" 2>/dev/null || pip install --no-input piexif==1.1.3

# self-check (diagnostic)
python3 -c "import piexif, PIL; print('piexif', piexif.VERSION, '| Pillow', PIL.__version__)"
