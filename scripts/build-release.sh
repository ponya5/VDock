#!/usr/bin/env bash
# Full release pipeline: freeze backend -> build frontend -> electron-builder.
# Produces installer artifacts in frontend/electron/dist-electron/.
# Prerequisites: ./setup.sh already ran (backend/venv + node_modules must exist).
# Extra arguments go to electron-builder, e.g. `--mac dir` for an unpacked app.
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
BUILDER_ARGS=()
# macOS without a Developer ID certificate: ad-hoc sign (DL-010). Unsigned
# apps are reported as "damaged" on Apple Silicon; ad-hoc ones get the
# System Settings > Privacy & Security > "Open Anyway" path. A configured
# certificate (CSC_LINK / CSC_NAME / keychain identity) is used as before.
if [[ "$(uname -s)" == "Darwin" && -z "${CSC_LINK:-}" && -z "${CSC_NAME:-}" ]] \
   && ! security find-identity -v -p codesigning 2>/dev/null | grep -q "Developer ID Application"; then
    echo "  No Developer ID certificate found - ad-hoc signing the macOS app."
    BUILDER_ARGS+=("-c.mac.identity=-")
fi
(cd "$PROJECT_ROOT/frontend/electron" && npx electron-builder ${BUILDER_ARGS[@]+"${BUILDER_ARGS[@]}"} "$@")

echo ""
echo "========================================"
echo "Release build complete!"
echo "Artifacts: frontend/electron/dist-electron/"
echo "========================================"
