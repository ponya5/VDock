#!/usr/bin/env bash
# ============================================================
#  VDock Setup Installer (macOS / Linux)
#  Installs all dependencies and creates a desktop launcher
#  Run this once before using ./launch.sh
# ============================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "  ${YELLOW}[WARN]${NC}  $*"; }
fail() {
  echo ""
  echo -e "  ${RED}[ERROR]${NC} $*"
  echo ""
  echo "  =========================================="
  echo "    Setup failed. Fix the error above and"
  echo "    run ./setup.sh again."
  echo "  =========================================="
  echo ""
  exit 1
}

echo ""
echo "  =========================================="
echo "    VDock  |  Setup Installer (macOS/Linux)"
echo "  =========================================="
echo ""

# ── [1/7] Python ─────────────────────────────────────────────
echo "  [1/7] Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
  fail "Python 3 not found. Install Python 3.9+ from https://www.python.org/downloads/ or via Homebrew: brew install python"
fi

PYTHON_VERSION="$(python3 --version 2>&1)"
ok "$PYTHON_VERSION"

PYTHON_MAJOR="$(python3 -c 'import sys; print(sys.version_info.major)')"
PYTHON_MINOR="$(python3 -c 'import sys; print(sys.version_info.minor)')"
if [[ "$PYTHON_MAJOR" -lt 3 ]] || { [[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -lt 9 ]]; }; then
  fail "Python 3.9+ required. Found ${PYTHON_VERSION}"
fi

# ── [2/7] Node.js ────────────────────────────────────────────
echo "  [2/7] Checking Node.js..."
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v node >/dev/null 2>&1; then
  fail "Node.js not found. Install Node.js 18+ from https://nodejs.org/ or via Homebrew: brew install node"
fi
ok "Node.js $(node --version)"

if ! command -v npm >/dev/null 2>&1; then
  fail "npm not found. Reinstall Node.js from https://nodejs.org/ or via Homebrew: brew install node"
fi
ok "npm $(npm --version)"

# ── [3/7] Python virtual environment ─────────────────────────
echo "  [3/7] Setting up Python virtual environment..."
VENV_ACTIVATE="$ROOT/backend/venv/bin/activate"
if [[ ! -f "$VENV_ACTIVATE" ]]; then
  echo "         Creating venv..."
  python3 -m venv "$ROOT/backend/venv" || fail "Failed to create virtual environment"
  ok "Virtual environment created"
else
  ok "Virtual environment already exists"
fi

# ── [4/7] Python dependencies ────────────────────────────────
echo "  [4/7] Installing backend dependencies..."
# shellcheck disable=SC1090
source "$VENV_ACTIVATE"

echo "         Upgrading pip..."
if ! python -m pip install --upgrade pip --quiet --disable-pip-version-check; then
  warn "pip upgrade failed (non-fatal, continuing)"
fi

if ! pip install -r "$ROOT/backend/requirements.txt" --quiet --disable-pip-version-check; then
  fail "pip install failed. Check your internet connection, or try running ./setup.sh again."
fi
ok "Backend dependencies installed"

# ── [5/7] Frontend Node dependencies ─────────────────────────
echo "  [5/7] Installing frontend dependencies..."
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo "         Running npm install in frontend/..."
  (
    cd "$ROOT/frontend"
    npm install --no-fund --no-audit
  ) || fail "npm install failed (frontend)"
  [[ -d "$ROOT/frontend/node_modules" ]] || fail "npm install failed (frontend) — node_modules missing"
  ok "Frontend node_modules installed"
else
  ok "frontend/node_modules already present"
fi

# ── [6/7] Electron Node dependencies ─────────────────────────
echo "  [6/7] Installing Electron dependencies..."
if [[ ! -d "$ROOT/frontend/electron/node_modules" ]]; then
  echo "         Running npm install in frontend/electron/..."
  (
    cd "$ROOT/frontend/electron"
    npm install --no-fund --no-audit
  ) || fail "npm install failed (electron)"
  [[ -d "$ROOT/frontend/electron/node_modules" ]] || fail "npm install failed (electron) — node_modules missing"
  ok "Electron node_modules installed"
else
  ok "frontend/electron/node_modules already present"
fi

# ── [7/7] Data directories ───────────────────────────────────
echo "  [7/7] Creating data directories..."
for data_dir in \
  "$ROOT/backend/data" \
  "$ROOT/backend/data/profiles" \
  "$ROOT/backend/data/uploads" \
  "$ROOT/backend/data/uploads/backgrounds" \
  "$ROOT/backend/data/uploads/button_backgrounds" \
  "$ROOT/backend/data/uploads/dashboard_backgrounds" \
  "$ROOT/backend/data/plugins" \
  "$ROOT/backend/data/themes"
do
  mkdir -p "$data_dir"
done
ok "Data directories ready"

# Make launch script executable
chmod +x "$ROOT/setup.sh" "$ROOT/launch.sh" 2>/dev/null || true

# ── Desktop launcher (macOS) ─────────────────────────────────
echo ""
echo "  Creating desktop launcher..."

DESKTOP_DIR="${HOME}/Desktop"
if [[ ! -d "$DESKTOP_DIR" ]]; then
  DESKTOP_DIR="$(osascript -e 'POSIX path of (path to desktop folder)' 2>/dev/null | sed 's:/$::' || true)"
fi
if [[ -z "${DESKTOP_DIR:-}" ]]; then
  DESKTOP_DIR="${HOME}/Desktop"
fi

COMMAND_PATH="${DESKTOP_DIR}/VDock.command"
cat > "$COMMAND_PATH" << EOF
#!/bin/bash
cd "$ROOT"
exec ./launch.sh
EOF
chmod +x "$COMMAND_PATH"

if [[ -f "$COMMAND_PATH" ]]; then
  ok "Desktop launcher created: VDock.command"
else
  warn "Could not create desktop launcher (non-fatal)"
fi

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "  =========================================="
echo "    Setup complete!"
echo "  =========================================="
echo ""
echo "  To launch VDock:"
if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "    - Double-click VDock.command on your Desktop, or"
fi
echo "    - Run: ./launch.sh from this folder"
echo ""
echo "  URLs (once running):"
echo "    Backend:   http://localhost:5000"
echo "    Frontend:  http://localhost:3000"
echo ""

read -r -p "  Start VDock now? [Y/N]: " START_NOW || START_NOW="N"
if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
  echo ""
  echo "  Starting VDock..."
  exec "$ROOT/launch.sh"
fi

echo ""
