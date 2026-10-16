#!/usr/bin/env bash
# ============================================================
#  VDock Launcher (macOS / Linux)
#  Starts backend, frontend, and Electron (or browser fallback)
# ============================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Prefer Homebrew Node/Python on Apple Silicon and Intel Macs
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

echo ""
echo "  =========================================="
echo "    VDock  |  Launcher"
echo "  =========================================="
echo ""

if [[ ! -f "$ROOT/backend/venv/bin/activate" ]]; then
  echo "  [ERROR] Virtual environment not found."
  echo "         Please run ./setup.sh first."
  echo ""
  read -r -p "  Press Enter to exit..." _
  exit 1
fi

# The launcher runs on VDock's own venv Python - the one setup.sh chose and
# the backend uses - not whatever python3 is on PATH, which may be missing in
# a Finder launch or be a newer, unsupported Python (DL-010).
VENV_PYTHON="$ROOT/backend/venv/bin/python"
if [[ ! -x "$VENV_PYTHON" ]] || ! "$VENV_PYTHON" -c 'import sys' >/dev/null 2>&1; then
  echo "  [ERROR] VDock's Python environment (backend/venv) no longer works:"
  echo "         the Python it was made with was moved, upgraded or uninstalled."
  echo "         Run ./setup.sh again - it rebuilds the environment."
  echo ""
  read -r -p "  Press Enter to exit..." _ || true
  exit 1
fi

exec "$VENV_PYTHON" "$ROOT/scripts/VDock-Launcher.py"
