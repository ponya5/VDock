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

MIN_PYTHON_VERSION_TUPLE="(3, 9)"
MIN_NODE_MAJOR_VERSION=20
PYTHON_BIN=""

# Homebrew's Node/Python first: Apple Silicon and Intel Macs both keep them
# outside the default PATH that Terminal/Finder launches give us.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

is_macos() {
  [[ "$(uname -s)" == "Darwin" ]]
}

# python3 can be macOS's /usr/bin stub, which pops an "install developer
# tools" dialog (or fails) until the Command Line Tools exist - skip it then.
is_usable_python() {
  local candidate="$1"
  local candidate_path
  candidate_path="$(command -v "$candidate" 2>/dev/null)" || return 1

  if is_macos && [[ "$candidate_path" == "/usr/bin/python3" ]] && ! xcode-select -p >/dev/null 2>&1; then
    return 1
  fi

  "$candidate" -c "import sys, venv, ensurepip; sys.exit(0 if sys.version_info >= $MIN_PYTHON_VERSION_TUPLE else 1)" >/dev/null 2>&1
}

find_python() {
  local candidate
  for candidate in python3 python3.13 python3.12 python3.11 python3.10 python3.9; do
    if is_usable_python "$candidate"; then
      PYTHON_BIN="$candidate"
      return 0
    fi
  done
  return 1
}

is_node_usable() {
  command -v node >/dev/null 2>&1 || return 1
  command -v npm >/dev/null 2>&1 || return 1

  local node_major_version
  node_major_version="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null)" || return 1
  [[ "$node_major_version" -ge "$MIN_NODE_MAJOR_VERSION" ]]
}

print_manual_install_help() {
  err "Python 3.9+ and Node.js ${MIN_NODE_MAJOR_VERSION}+ are required."
  echo "         Python:  https://www.python.org/downloads/"
  echo "         Node.js: https://nodejs.org/"
  if is_macos; then
    echo "         Or with Homebrew (https://brew.sh):  brew install python node"
  fi
  echo "         Then run ./setup.sh again."
}

install_with_homebrew() {
  local formulas=("$@")

  if ! is_macos || ! command -v brew >/dev/null 2>&1; then
    return 1
  fi

  warn "Missing: ${formulas[*]}"
  local answer
  read -r -p "  Install it now with Homebrew (brew install ${formulas[*]})? [Y/n]: " answer || return 1
  if [[ "$answer" =~ ^[Nn]$ ]]; then
    return 1
  fi

  brew install "${formulas[@]}" || return 1
  hash -r
}

ensure_prerequisites() {
  local missing_formulas=()
  find_python || missing_formulas+=(python)
  is_node_usable || missing_formulas+=(node)

  if [[ ${#missing_formulas[@]} -eq 0 ]]; then
    return 0
  fi

  if ! install_with_homebrew "${missing_formulas[@]}"; then
    print_manual_install_help
    return 1
  fi

  if ! find_python || ! is_node_usable; then
    print_manual_install_help
    return 1
  fi
}

install_dependencies() {
  echo ""
  echo "  =========================================="
  echo "    Installing VDock dependencies"
  echo "  =========================================="
  echo ""

  echo "  [1/7] Checking Python and Node.js..."
  ensure_prerequisites || return 1
  ok "$("$PYTHON_BIN" --version 2>&1)"
  ok "Node.js $(node --version)"
  ok "npm $(npm --version)"

  echo "  [2/7] Python virtual environment..."
  local venv_activate="$ROOT/backend/venv/bin/activate"
  if [[ ! -f "$venv_activate" ]]; then
    echo "           Creating venv..."
    "$PYTHON_BIN" -m venv "$ROOT/backend/venv" || return 1
    ok "Virtual environment created"
  else
    ok "Virtual environment already exists"
  fi

  echo "  [3/7] Backend dependencies..."
  # shellcheck disable=SC1090
  source "$venv_activate"
  python -m pip install --upgrade pip --quiet --disable-pip-version-check >/dev/null 2>&1 || warn "pip upgrade failed (non-fatal)"
  pip install -r "$ROOT/backend/requirements.txt" --quiet --disable-pip-version-check || return 1
  ok "Backend dependencies installed"

  # Always run: npm install is a no-op when node_modules already matches the
  # lockfile, and picks up packages added by a git pull when it doesn't.
  echo "  [4/7] Frontend dependencies..."
  ( cd "$ROOT/frontend" && npm install --no-fund --no-audit ) || { err "npm install failed in frontend"; return 1; }
  ok "Frontend dependencies installed"

  echo "  [5/7] Electron dependencies..."
  ( cd "$ROOT/frontend/electron" && npm install --no-fund --no-audit ) || { err "npm install failed in frontend/electron"; return 1; }
  ok "Electron dependencies installed"

  echo "  [6/7] Data directories..."
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

  echo "  [7/7] Integrations..."
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

port_has_listener() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

port_serves_vdock() {
  curl -s -m 2 "http://127.0.0.1:$1/api/health" 2>/dev/null | grep -q '"uptime_s"'
}

find_free_port() {
  local candidate_port="$1"
  while port_has_listener "$candidate_port"; do
    candidate_port=$((candidate_port + 1))
  done
  echo "$candidate_port"
}

configure_ports() {
  echo ""
  echo "  =========================================="
  echo "    Port configuration"
  echo "  =========================================="
  echo ""

  local cur_frontend_port=3000
  if [[ -f "$ROOT/frontend/.env" ]]; then
    local found
    found="$(grep -m1 '^VITE_PORT=' "$ROOT/frontend/.env" 2>/dev/null | cut -d= -f2)" || true
    [[ -n "$found" ]] && cur_frontend_port="$found"
  fi
  local cur_backend_port=5000
  if [[ -f "$ROOT/backend/.env" ]]; then
    local found
    found="$(grep -m1 '^PORT=' "$ROOT/backend/.env" 2>/dev/null | cut -d= -f2)" || true
    [[ -n "$found" ]] && cur_backend_port="$found"
  fi

  # macOS AirPlay Receiver (and other apps) squat on 5000 and answer 403 to
  # everything, which leaves VDock's window blank. Never default to a port
  # another app already owns - a running VDock backend is fine to keep.
  if port_has_listener "$cur_backend_port" && ! port_serves_vdock "$cur_backend_port"; then
    local free_backend_port
    free_backend_port="$(find_free_port "$((cur_backend_port + 1))")"
    warn "Port $cur_backend_port is used by another app (on macOS: AirPlay Receiver)."
    warn "Defaulting the backend to port $free_backend_port instead."
    cur_backend_port="$free_backend_port"
  fi

  local frontend_port="$cur_frontend_port"
  local backend_port="$cur_backend_port"

  if [[ "${1:-}" != "silent" ]]; then
    echo "  3000/5000 are common defaults - change them if another app already"
    echo "  uses one. Press Enter to keep the current value shown in [brackets]."
    echo ""
    read -r -p "  Frontend port [$cur_frontend_port]: " frontend_port || frontend_port=""
    [[ -z "$frontend_port" ]] && frontend_port="$cur_frontend_port"
    read -r -p "  Backend port [$cur_backend_port]: " backend_port || backend_port=""
    [[ -z "$backend_port" ]] && backend_port="$cur_backend_port"

    if ! [[ "$frontend_port" =~ ^[0-9]+$ ]]; then
      warn "\"$frontend_port\" is not a valid port number. Using $cur_frontend_port."
      frontend_port="$cur_frontend_port"
    fi
    if ! [[ "$backend_port" =~ ^[0-9]+$ ]]; then
      warn "\"$backend_port\" is not a valid port number. Using $cur_backend_port."
      backend_port="$cur_backend_port"
    fi
    if [[ "$frontend_port" == "$backend_port" ]]; then
      warn "Frontend and backend ports must differ. Keeping current values."
      frontend_port="$cur_frontend_port"
      backend_port="$cur_backend_port"
    fi
  fi

  touch "$ROOT/backend/.env"
  grep -v -E '^(PORT=|CORS_ORIGINS=)' "$ROOT/backend/.env" > "$ROOT/backend/.env.tmp" || true
  {
    cat "$ROOT/backend/.env.tmp"
    echo "PORT=$backend_port"
    echo "CORS_ORIGINS=http://localhost:$frontend_port,http://127.0.0.1:$frontend_port"
  } > "$ROOT/backend/.env"
  rm -f "$ROOT/backend/.env.tmp"

  touch "$ROOT/frontend/.env"
  grep -v -E '^(VITE_PORT=|VITE_BACKEND_PORT=)' "$ROOT/frontend/.env" > "$ROOT/frontend/.env.tmp" || true
  {
    cat "$ROOT/frontend/.env.tmp"
    echo "VITE_PORT=$frontend_port"
    echo "VITE_BACKEND_PORT=$backend_port"
  } > "$ROOT/frontend/.env"
  rm -f "$ROOT/frontend/.env.tmp"

  ok "Frontend port: $frontend_port"
  ok "Backend port:  $backend_port"

  FRONTEND_PORT="$frontend_port"
  BACKEND_PORT="$backend_port"
}

# VDock serves frontend/dist, which git does not track - without this step a
# pull or reinstall keeps showing the previously built UI. Runs after
# configure_ports because the ports in frontend/.env are baked into the bundle.
build_frontend() {
  echo ""
  echo "  Building the frontend..."
  export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
  ( cd "$ROOT/frontend" && npm run build ) || { err "Frontend build failed. See the output above."; return 1; }
  ok "Frontend built (frontend/dist)"
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
exec bash ./launch.sh
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
exec bash ./launch.sh
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
  exec bash "$ROOT/launch.sh"
}

show_menu() {
  clear
  echo ""
  echo "  ========================================================"
  echo "    VDock Setup"
  echo "  ========================================================"
  echo ""
  echo "    [1] Full setup (recommended)"
  echo "        Install deps, build the frontend, desktop launcher"
  echo ""
  echo "    [2] Install dependencies only"
  echo "        Deps + frontend build, no desktop launcher"
  echo ""
  echo "    [3] Create desktop launcher only"
  echo ""
  echo "    [4] Configure ports"
  echo "        Change which localhost ports VDock uses"
  echo ""
  echo "    [5] Launch VDock now"
  echo ""
  echo "    [6] Exit"
  echo ""
}

run_full_setup() {
  echo ""
  echo "  This takes a few minutes the first time (downloads Python and"
  echo "  Node packages). Ports are chosen automatically; change them any"
  echo "  time with: ./setup.sh --ports"

  install_dependencies || return 1
  configure_ports silent
  build_frontend || return 1
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
  echo "  VDock opens at: http://localhost:${BACKEND_PORT:-5000}"
  echo ""
  read -r -p "  Start VDock now? [Y/n]: " start_now || start_now="N"
  if [[ ! "$start_now" =~ ^[Nn]$ ]]; then
    launch_vdock
  fi
}

# A fresh clone has no venv yet: skip the menu and just do the right thing.
run_first_time_setup_if_needed() {
  if [[ -f "$ROOT/backend/venv/bin/activate" ]]; then
    return 0
  fi

  echo ""
  echo "  Welcome to VDock! Setting everything up for you..."
  if run_full_setup; then
    exit 0
  fi

  echo ""
  read -r -p "  Setup did not finish. Press Enter to open the setup menu..." _ || exit 1
}

handle_cli_flag() {
  case "${1:-}" in
    --full) run_full_setup silent; exit $? ;;
    --deps) install_dependencies && build_frontend; exit $? ;;
    --shortcut) create_desktop_launcher; exit $? ;;
    --ports) configure_ports; exit $? ;;
    --launch) launch_vdock; exit $? ;;
  esac
}

handle_cli_flag "${1:-}"
run_first_time_setup_if_needed

while true; do
  show_menu
  read -r -p "  Choose an option [1-6]: " menu_choice || menu_choice="6"

  case "$menu_choice" in
    1)
      run_full_setup || echo ""
      read -r -p "  Press Enter to continue..." _
      ;;
    2)
      { install_dependencies && build_frontend; } || echo ""
      read -r -p "  Press Enter to continue..." _
      ;;
    3)
      create_desktop_launcher
      read -r -p "  Press Enter to continue..." _
      ;;
    4)
      configure_ports
      read -r -p "  Press Enter to continue..." _
      ;;
    5)
      launch_vdock || read -r -p "  Press Enter to continue..." _
      ;;
    6)
      exit 0
      ;;
    *)
      echo ""
      echo -e "  ${CYAN}Invalid choice.${NC} Press Enter to try again..."
      read -r _ || true
      ;;
  esac
done
