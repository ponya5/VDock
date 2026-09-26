#!/usr/bin/env bash
# Freeze the VDock backend into dist/vdock-backend/ via PyInstaller.
# Consumed by electron-builder's extraResources, or runnable standalone.
# Requires backend/venv — run ./setup.sh first.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_PYTHON="$BACKEND_DIR/venv/bin/python"
DIST_DIR="$PROJECT_ROOT/dist"

echo "========================================"
echo "VDock Backend Freeze (PyInstaller)"
echo "========================================"

if [ ! -x "$VENV_PYTHON" ]; then
    echo "ERROR: backend venv not found at $VENV_PYTHON"
    echo "Run ./setup.sh first."
    exit 1
fi

echo "[1/2] Installing build dependencies..."
"$VENV_PYTHON" -m pip install -q -r "$BACKEND_DIR/requirements-build.txt"

echo "[2/2] Running PyInstaller spec..."
(cd "$BACKEND_DIR" && "$VENV_PYTHON" -m PyInstaller vdock-backend.spec \
    --distpath "$DIST_DIR" --workpath "$DIST_DIR/build" --noconfirm)

EXE="$DIST_DIR/vdock-backend/vdock-backend"
if [ -x "$EXE" ]; then
    echo ""
    echo "OK - frozen backend at $EXE"
else
    echo "ERROR: expected output missing: $EXE"
    exit 1
fi
