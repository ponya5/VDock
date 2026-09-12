#!/usr/bin/env bash
# ============================================================
#  VDock Setup — single installer for end users (macOS / Linux)
# ============================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "  ${YELLOW}[WARN]${NC}  $*"; }
err()  { echo -e "  ${RED}[ERROR]${NC} $*"; }

install_dependencies() {
  echo ""
  echo "  =========================================="
  echo "    Installing VDock dependencies"
  echo "  =========================================="
  echo ""

  echo "  [1/8] Checking Python..."
  if ! command -v python3 >/dev/null 2>&1; then
    err "Python 3 not found. Install 3.9+ from https://www.python.org/downloads/"
    return 1
  fi
  ok "$(python3 --version 2>&1)"

  local py_major py_minor
  py_major="$(python3 -c 'import sys; print(sys.version_info.major)')"
  py_minor="$(python3 -c 'import sys; print(sys.version_info.minor)')"
  if [[ "$py_major" -lt 3 ]] || { [[ "$py_major" -eq 3 ]] && [[ "$py_minor" -lt 9 ]]; }; then
    err "Python 3.9+ required."
    return 1
  fi

  echo "  [2/8] Checking Node.js..."
  export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
  if ! command -v node >/dev/null 2>&1; then
    err "Node.js not found. Install 18+ from https://nodejs.org/"
    return 1
  fi
  ok "Node.js $(node --version)"
  ok "npm $(npm --version)"

  echo "  [3/8] Python virtual environment..."
  local venv_activate="$ROOT/backend/venv/bin/activate"
  if [[ ! -f "$venv_activate" ]]; then
    echo "           Creating venv..."
    python3 -m venv "$ROOT/backend/venv" || return 1
    ok "Virtual environment created"
  else
    ok "Virtual environment already exists"
  fi

  echo "  [4/8] Backend dependencies..."
  # shellcheck disable=SC1090
  source "$venv_activate"
  python -m pip install --upgrade pip --quiet --disable-pip-version-check >/dev/null 2>&1 || warn "pip upgrade failed (non-fatal)"
  pip install -r "$ROOT/backend/requirements.txt" --quiet --disable-pip-version-check || return 1
  ok "Backend dependencies installed"

  echo "  [5/8] Frontend dependencies..."
  if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
    ( cd "$ROOT/frontend" && npm install --no-fund --no-audit ) || return 1
    ok "Frontend node_modules installed"
  else
    ok "frontend/node_modules already present"
  fi

  echo "  [6/8] Electron dependencies..."
  if [[ ! -d "$ROOT/frontend/electron/node_modules" ]]; then
    ( cd "$ROOT/frontend/electron" && npm install --no-fund --no-audit ) || return 1
    ok "Electron node_modules installed"
  else
    ok "frontend/electron/node_modules already present"
  fi

  echo "  [7/8] Data directories..."
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

  echo "  [8/8] Integrations..."
  if [ ! -f "$ROOT/backend/.env" ] && [ -f "$ROOT/backend/.env.example" ]; then
    cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
    ok "Created backend/.env from the example"
  else
    ok "backend/.env already exists"
  fi

  # VDock works with none of these. Each pack detects what it can use and greys
  # out only the actions it cannot run, so this is information, not a
  # requirement.
  found_any=""
  if command -v claude >/dev/null 2>&1; then
    ok "Claude Code CLI detected - Claude actions enabled"; found_any=1
  else
    echo "  [ --]  Claude Code CLI not found - https://claude.com/product/claude-code"
  fi
  if command -v gh >/dev/null 2>&1; then
    ok "GitHub CLI detected - GitHub actions enabled"; found_any=1
  else
    echo "  [ --]  GitHub CLI not found - https://cli.github.com"
  fi
  if command -v git >/dev/null 2>&1; then
    ok "Git detected - repository-aware actions enabled"
  else
    echo "  [ --]  Git not found - repo detection falls back to a default folder"
  fi
  if [ -z "$found_any" ]; then
    echo "         No integration CLIs found. VDock still works fully;"
    echo "         the Claude and GitHub buttons will show why they are unavailable."
  fi

  chmod +x "$ROOT/setup.sh" "$ROOT/launch.sh" 2>/dev/null || true
  return 0
}

create_desktop_launcher() {
  echo ""
  echo "  Creating desktop launcher..."

  local desktop_dir="${HOME}/Desktop"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    if [[ ! -d "$desktop_dir" ]]; then
      desktop_dir="$(osascript -e 'POSIX path of (path to desktop folder)' 2>/dev/null | sed 's:/$::' || true)"
    fi
    [[ -n "${desktop_dir:-}" ]] || desktop_dir="${HOME}/Desktop"

    local command_path="${desktop_dir}/VDock.command"
    cat > "$command_path" << EOF
#!/bin/bash
cd "$ROOT"
exec ./launch.sh
EOF
    chmod +x "$command_path"
    if [[ -f "$command_path" ]]; then
      ok "Desktop launcher created: VDock.command"
    else
      warn "Could not create desktop launcher"
    fi
    return 0
  fi

  if [[ -d "${XDG_DESKTOP_DIR:-}" ]]; then
    desktop_dir="$XDG_DESKTOP_DIR"
  elif [[ -d "${HOME}/Desktop" ]]; then
    desktop_dir="${HOME}/Desktop"
  fi

  local shell_launcher="${desktop_dir}/VDock.sh"
  cat > "$shell_launcher" << EOF
#!/usr/bin/env bash
cd "$ROOT"
exec ./launch.sh
EOF
  chmod +x "$shell_launcher"

  local desktop_entry="${desktop_dir}/vdock.desktop"
  cat > "$desktop_entry" << EOF
[Desktop Entry]
Type=Application
Name=VDock
Comment=Virtual Stream Deck
Exec=$shell_launcher
Path=$ROOT
Terminal=true
Categories=Utility;
EOF
  chmod +x "$desktop_entry" 2>/dev/null || true

  if [[ -f "$shell_launcher" ]]; then
    ok "Desktop launcher created: VDock.sh"
  else
    warn "Could not create desktop launcher"
  fi
}

launch_vdock() {
  if [[ ! -f "$ROOT/backend/venv/bin/activate" ]]; then
    err "Run Full setup first (option 1)."
    return 1
  fi
  echo ""
  echo "  Starting VDock..."
  exec "$ROOT/launch.sh"
}

show_menu() {
  clear
  echo ""
  echo "  ========================================================"
  echo "    VDock Setup"
  echo "  ========================================================"
  echo ""
  echo "    [1] Full setup (recommended)"
  echo "        Install deps + create desktop launcher"
  echo ""
  echo "    [2] Install dependencies only"
  echo ""
  echo "    [3] Create desktop launcher only"
  echo ""
  echo "    [4] Launch VDock now"
  echo ""
  echo "    [5] Exit"
  echo ""
}

run_full_setup() {
  install_dependencies || return 1
  create_desktop_launcher
  echo ""
  echo "  =========================================="
  echo "    Setup complete!"
  echo "  =========================================="
  echo ""
  echo "  Launch VDock:"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "    - Double-click VDock.command on your Desktop"
  fi
  echo "    - Or run: ./launch.sh"
  echo ""
  read -r -p "  Start VDock now? [Y/N]: " start_now || start_now="N"
  if [[ "$start_now" =~ ^[Yy]$ ]]; then
    launch_vdock
  fi
}

handle_cli_flag() {
  case "${1:-}" in
    --full) run_full_setup; exit $? ;;
    --deps) install_dependencies; exit $? ;;
    --shortcut) create_desktop_launcher; exit $? ;;
    --launch) launch_vdock; exit $? ;;
  esac
}

handle_cli_flag "${1:-}"

while true; do
  show_menu
  read -r -p "  Choose an option [1-5]: " menu_choice || menu_choice="5"

  case "$menu_choice" in
    1)
      run_full_setup || echo ""
      read -r -p "  Press Enter to continue..." _
      ;;
    2)
      install_dependencies || echo ""
      read -r -p "  Press Enter to continue..." _
      ;;
    3)
      create_desktop_launcher
      read -r -p "  Press Enter to continue..." _
      ;;
    4)
      launch_vdock || read -r -p "  Press Enter to continue..." _
      ;;
    5)
      exit 0
      ;;
    *)
      echo ""
      echo -e "  ${CYAN}Invalid choice.${NC} Press Enter to try again..."
      read -r _ || true
      ;;
  esac
done
