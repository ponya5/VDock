#!/usr/bin/env bash
# Run the same checks CI runs, locally, in one command.
#   backend pytest -> vue-tsc -> vitest -> production build
# Prints one PASS/FAIL line per step; exits non-zero if any step failed.
# Uses backend/venv when present, otherwise python3 on PATH.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/backend/venv/bin/python"
[ -x "$PY" ] || PY="python3"

failed=0
summary=""

step() {
  local name="$1" dir="$2"
  shift 2
  echo
  echo "=== $name ==="
  if (cd "$dir" && "$@"); then
    summary+="PASS  $name"$'\n'
  else
    summary+="FAIL  $name"$'\n'
    failed=1
  fi
}

# pyautogui / pynput need a display even to import (same as CI).
PYTEST=("$PY" -m pytest tests -q)
if [ -z "${DISPLAY:-}" ] && command -v xvfb-run >/dev/null 2>&1; then
  PYTEST=(xvfb-run -a "${PYTEST[@]}")
fi

step "Backend tests (pytest)"  "$ROOT/backend"  "${PYTEST[@]}"
step "Type check (vue-tsc)"    "$ROOT/frontend" npx vue-tsc --noEmit
step "Frontend tests (vitest)" "$ROOT/frontend" npx vitest run
step "Build (vite)"            "$ROOT/frontend" npm run build

echo
echo "=== Summary ==="
printf '%s' "$summary"
exit "$failed"
