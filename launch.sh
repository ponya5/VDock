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

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "  [ERROR] Python not found. Install Python 3.9+."
  echo ""
  read -r -p "  Press Enter to exit..." _
  exit 1
fi

exec "$PYTHON_BIN" "$ROOT/scripts/VDock-Launcher.py"
