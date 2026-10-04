#!/usr/bin/env bash
# Environment provisioning for the March 2026 studio billing task.
# Ensures the icalendar-events-parser skill's Node.js dependencies exist.
set -uo pipefail

install_skill_deps() {
  local d="$1"
  [ -f "$d/package.json" ] || return 0
  if [ -d "$d/node_modules/icalendar-events" ] && [ -d "$d/node_modules/luxon" ]; then
    echo "setup: $d node_modules already present"
  else
    echo "setup: installing pinned npm deps into $d"
    (cd "$d" && npm install --no-input --no-fund --no-audit --no-save \
       icalendar-events@1.1.1 luxon@3.7.2) \
      || (cd "$d" && npm install --no-input --no-fund --no-audit) \
      || echo "setup: WARNING npm install failed for $d"
  fi
  chmod +x "$d/index.js" 2>/dev/null || true
}

install_skill_deps "${PWD}/_skill_ref"
install_skill_deps "/app/_skill_ref"

# self-check (diagnostic only)
node --version || true
ls -d "${PWD}/_skill_ref/node_modules/icalendar-events" 2>/dev/null \
  || ls -d /app/_skill_ref/node_modules/icalendar-events 2>/dev/null \
  || echo "setup: WARNING skill deps not found"
exit 0
