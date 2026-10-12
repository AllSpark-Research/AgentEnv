#!/bin/bash
# No extra dependencies: the skill script, task inputs, and verifier use python3 stdlib only.
set -e
python3 -c "import json, re, sys; assert sys.version_info >= (3, 8)"
# none
