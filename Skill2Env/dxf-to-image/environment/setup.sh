#!/usr/bin/env bash
# Environment provisioning for the DXF review-package task (idempotent).
set -e

pip install --no-input ezdxf==1.4.4 matplotlib==3.11.1 Pillow==12.3.0

# self-check (diagnostic)
pip freeze | grep -iE '^(ezdxf|matplotlib|pillow)==' || true
python3 -c "import ezdxf, matplotlib, PIL; print('deps ok:', ezdxf.__version__, matplotlib.__version__, PIL.__version__)"
