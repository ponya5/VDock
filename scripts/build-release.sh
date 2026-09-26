#!/usr/bin/env bash
# Full release pipeline: freeze backend -> build frontend -> electron-builder.
# Produces installer artifacts in frontend/electron/dist-electron/.
# Prerequisites: ./setup.sh already ran (backend/venv + node_modules must exist).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "VDock Release Build"
echo "========================================"

echo ""
echo "[1/3] Freezing backend..."
"$SCRIPT_DIR/build-backend.sh"

echo ""
echo "[2/3] Building frontend..."
(cd "$PROJECT_ROOT/frontend" && npm run build)

echo ""
echo "[3/3] Packaging Electron app..."
(cd "$PROJECT_ROOT/frontend/electron" && npx electron-builder)

echo ""
echo "========================================"
echo "Release build complete!"
echo "Artifacts: frontend/electron/dist-electron/"
echo "========================================"
