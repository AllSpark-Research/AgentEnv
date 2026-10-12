#!/usr/bin/env bash
# Environment provisioning for the catalog preflight task.
# pymupdf and pillow are already in the base image; install pinned copies only if missing (idempotent guard).
set -e

python3 - <<'EOF' || pip install --no-input pymupdf==1.28.0 pillow==12.3.0
import fitz, PIL  # noqa
EOF

# self-check (diagnostic)
python3 -c "import fitz, PIL; print('pymupdf', fitz.VersionBind if hasattr(fitz,'VersionBind') else 'ok', '| pillow', PIL.__version__)" || true
pip freeze 2>/dev/null | grep -i -E '^(pymupdf|pillow)==' || true
