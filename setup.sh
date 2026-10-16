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

MIN_NODE_MAJOR_VERSION=20
PYTHON_BIN=""

# Supported Python window (DL-010). 3.15 is too new: several dependencies
# (pywinrt on Windows, PyInstaller for release builds) have no 3.15 builds
# yet, and pip then fails half-way. 3.9 still works (it is the Command Line
# Tools python3 on a stock Mac) but is end-of-life.
MIN_PYTHON_MINOR=9
MAX_PYTHON_MINOR=14
RECOMMENDED_PYTHON="3.13"
# Best first: the newest well-supported releases, then the rest.
PREFERRED_PYTHON_MINORS=(13 12 14 11 10 9)
# Versioned Pythons that are often not on PATH: Homebrew kegs (Apple Silicon
# and Intel) and python.org installers. MINOR is replaced by 9..14.
VDOCK_PYTHON_SEARCH_DIRS="${VDOCK_PYTHON_SEARCH_DIRS-/opt/homebrew/opt/python@3.MINOR/bin /usr/local/opt/python@3.MINOR/bin /Library/Frameworks/Python.framework/Versions/3.MINOR/bin}"
# "3.15 (/opt/homebrew/bin/python3)" when only an unsupported Python exists.
UNSUPPORTED_PYTHON=""
VENV_PROBLEM=""

# Homebrew's Node/Python first: Apple Silicon and Intel Macs both keep them
# outside the default PATH that Terminal/Finder launches give us.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

is_macos() {
  [[ "$(uname -s)" == "Darwin" ]]
}

# Prompts are "[Y/n]": Enter means yes, and only an explicit yes counts as
# yes. Anything else ("n", "no", a typo) must never start an install/launch.
is_yes_answer() {
  local answer="$1"
  [[ -z "$answer" || "$answer" =~ ^[Yy]([Ee][Ss])?$ ]]
}

python_minor_supported() {
  local version="$1"
  [[ "$version" =~ ^3\.([0-9]+)$ ]] || return 1
  local minor="${BASH_REMATCH[1]}"
  (( minor >= MIN_PYTHON_MINOR && minor <= MAX_PYTHON_MINOR ))
}

# "3.13" for an interpreter, nothing (and failure) when it does not run.
python_version_of() {
  "$1" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null
}

# python3 can be macOS's /usr/bin stub, which pops an "install developer
# tools" dialog (or fails) until the Command Line Tools exist - skip it then.
# Debian/Ubuntu ship python3 without venv/ensurepip (python3-venv).
is_usable_python() {
  local candidate_path="$1"

  if is_macos && [[ "$candidate_path" == "/usr/bin/python3" ]] && ! xcode-select -p >/dev/null 2>&1; then
    return 1
  fi

  "$candidate_path" -c "import sys, venv, ensurepip" >/dev/null 2>&1
}

python_candidates() {
  local minor dir
  for minor in "${PREFERRED_PYTHON_MINORS[@]}"; do
    echo "python3.$minor"
    for dir in $VDOCK_PYTHON_SEARCH_DIRS; do
      echo "${dir//MINOR/$minor}/python3.$minor"
    done
  done
  echo python3
  echo python
}

python_preference_rank() {
  local version="$1" rank=0 minor
  for minor in "${PREFERRED_PYTHON_MINORS[@]}"; do
    if [[ "$version" == "3.$minor" ]]; then
      echo "$rank"
      return 0
    fi
    rank=$((rank + 1))
  done
  echo 99
}

# Picks the best supported interpreter into PYTHON_BIN (3.13 > 3.12 > 3.14 >
# 3.11 > 3.10 > 3.9), whatever it is called. Remembers an unsupported one in
# UNSUPPORTED_PYTHON so the error can say what was found.
find_python() {
  PYTHON_BIN=""
  UNSUPPORTED_PYTHON=""
  local best_rank=99 candidate candidate_path version rank
  while IFS= read -r candidate; do
    candidate_path="$(command -v "$candidate" 2>/dev/null)" || continue
    [[ -n "$candidate_path" ]] || continue
    # The CLT stub would pop an install dialog even for a version query.
    if is_macos && [[ "$candidate_path" == "/usr/bin/python3" ]] && ! xcode-select -p >/dev/null 2>&1; then
      continue
    fi
    version="$(python_version_of "$candidate_path")" || continue
    [[ -n "$version" ]] || continue
    if ! python_minor_supported "$version"; then
      [[ -n "$UNSUPPORTED_PYTHON" ]] || UNSUPPORTED_PYTHON="$version ($candidate_path)"
      continue
    fi
    is_usable_python "$candidate_path" || continue
    rank="$(python_preference_rank "$version")"
    if (( rank < best_rank )); then
      best_rank="$rank"
      PYTHON_BIN="$candidate_path"
    fi
  done < <(python_candidates)
  [[ -n "$PYTHON_BIN" ]]
}

report_unsupported_python() {
  [[ -n "$UNSUPPORTED_PYTHON" ]] || return 0
  warn "Found Python $UNSUPPORTED_PYTHON, but VDock needs Python 3.$MIN_PYTHON_MINOR-3.$MAX_PYTHON_MINOR."
  echo "         Some of its packages have no builds for that version yet. Install"
  echo "         Python $RECOMMENDED_PYTHON next to it - setup then picks it automatically."
}

# OK when backend/venv's interpreter runs, is supported, and is the version
# the venv was made with. A venv made by mise "latest" or a Homebrew python
# that was upgraded or removed fails here and gets recreated. VENV_PROBLEM
# says why.
venv_python_ok() {
  local venv_dir="$1"
  local venv_python="$venv_dir/bin/python"
  VENV_PROBLEM=""
  if [[ ! -x "$venv_python" ]]; then
    VENV_PROBLEM="its Python is missing"
    return 1
  fi
  local version
  version="$(python_version_of "$venv_python")" || true
  if [[ -z "$version" ]]; then
    VENV_PROBLEM="its Python no longer runs (moved or uninstalled)"
    return 1
  fi
  if ! python_minor_supported "$version"; then
    VENV_PROBLEM="it uses Python $version, which VDock does not support"
    return 1
  fi
  local recorded
  recorded="$(sed -n -E 's/^version(_info)?[[:space:]]*=[[:space:]]*([0-9]+\.[0-9]+).*/\2/p' "$venv_dir/pyvenv.cfg" 2>/dev/null | head -n 1)" || true
  if [[ -n "$recorded" && "$recorded" != "$version" ]]; then
    VENV_PROBLEM="it was made with Python $recorded but now runs $version"
    return 1
  fi
}

# pip's own ERROR lines plus what they usually mean - never just "check your
# connection" when the real problem is a package with no build for this Python.
report_pip_failure() {
  local log_file="$1" venv_python="$2"
  local version
  version="$(python_version_of "$venv_python")" || true
  err "Installing the backend's Python packages failed (Python ${version:-?}, $(uname -m))."
  grep -E '^(ERROR|error):' "$log_file" 2>/dev/null | tail -n 4 | sed 's/^/           /' || true
  if grep -qiE 'No matching distribution|Could not find a version that satisfies|requires a different Python|Failed (building|to build)|subprocess-exited-with-error' "$log_file" 2>/dev/null; then
    local brew_hint=""
    is_macos && brew_hint=" (brew install python@$RECOMMENDED_PYTHON)"
    echo "         A package has no ready-made build for Python ${version:-?} on this computer."
    echo "         Install Python $RECOMMENDED_PYTHON$brew_hint, then run:"
    echo "           rm -rf backend/venv && ./setup.sh"
  elif grep -qiE 'connection|timed out|Temporary failure in name resolution|SSLError|ProxyError|Could not fetch URL' "$log_file" 2>/dev/null; then
    echo "         pip could not reach the package index - check your internet connection or proxy."
  fi
  echo "         Full log: $log_file"
}

is_node_usable() {
  command -v node >/dev/null 2>&1 || return 1
  command -v npm >/dev/null 2>&1 || return 1

  local node_major_version
  node_major_version="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null)" || return 1
  [[ "$node_major_version" -ge "$MIN_NODE_MAJOR_VERSION" ]]
}

print_manual_install_help() {
  err "Python 3.$MIN_PYTHON_MINOR-3.$MAX_PYTHON_MINOR ($RECOMMENDED_PYTHON recommended) and Node.js ${MIN_NODE_MAJOR_VERSION}+ are required."
  echo "         Python:  https://www.python.org/downloads/ (pick $RECOMMENDED_PYTHON)"
  echo "         Node.js: https://nodejs.org/"
  if is_macos; then
    echo "         Or with Homebrew (https://brew.sh):  brew install python@$RECOMMENDED_PYTHON node"
  elif [[ "$(uname -s)" == "Linux" ]]; then
    echo "         Debian/Ubuntu: sudo apt install python3 python3-venv nodejs npm"
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
  if ! is_yes_answer "$answer"; then
    return 1
  fi

  brew install "${formulas[@]}" || return 1
  hash -r
}

ensure_prerequisites() {
  local missing_formulas=()
  if ! find_python; then
    report_unsupported_python
    missing_formulas+=("python@$RECOMMENDED_PYTHON")
  fi
  is_node_usable || missing_formulas+=(node)

  if [[ ${#missing_formulas[@]} -eq 0 ]]; then
    return 0
  fi

  if ! install_with_homebrew "${missing_formulas[@]}"; then
    print_manual_install_help
    return 1
  fi

  if ! find_python || ! is_node_usable; then
    report_unsupported_python
    print_manual_install_help
    return 1
  fi
}

# npm is moving to block dependency install scripts by default, and Electron
# downloads its runtime in one. Without the runtime the VDock window cannot
# open, so run the download ourselves whenever npm did not.
ensure_electron_binary() {
  local electron_package_dir="$ROOT/frontend/electron/node_modules/electron"
  if [[ -f "$electron_package_dir/path.txt" ]]; then
    return 0
  fi

  echo "           Downloading the Electron runtime..."
  if ! ( cd "$electron_package_dir" && node install.js ); then
    err "Electron download failed. Check your connection and run ./setup.sh again."
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
  ok "$("$PYTHON_BIN" --version 2>&1) ($PYTHON_BIN)"
  if [[ "$(python_version_of "$PYTHON_BIN")" == "3.$MIN_PYTHON_MINOR" ]]; then
    warn "Python 3.$MIN_PYTHON_MINOR is end-of-life. VDock runs on it, but Python $RECOMMENDED_PYTHON is recommended."
  fi
  ok "Node.js $(node --version)"
  ok "npm $(npm --version)"

  echo "  [2/7] Python virtual environment..."
  local venv_dir="$ROOT/backend/venv"
  if [[ -e "$venv_dir" ]] && ! venv_python_ok "$venv_dir"; then
    warn "backend/venv can't be used: $VENV_PROBLEM. Recreating it."
    rm -rf "$venv_dir"
  fi
  if [[ ! -x "$venv_dir/bin/python" ]]; then
    echo "           Creating venv with $("$PYTHON_BIN" --version 2>&1)..."
    "$PYTHON_BIN" -m venv "$venv_dir" || { err "Could not create backend/venv with $PYTHON_BIN"; return 1; }
    ok "Virtual environment created"
  else
    ok "Virtual environment already exists ($("$venv_dir/bin/python" --version 2>&1))"
  fi

  echo "  [3/7] Backend dependencies..."
  local venv_python="$venv_dir/bin/python"
  local pip_log="$ROOT/backend/data/pip-install.log"
  mkdir -p "$ROOT/backend/data"
  "$venv_python" -m pip install --upgrade pip --quiet --disable-pip-version-check >/dev/null 2>&1 || warn "pip upgrade failed (non-fatal)"
  echo "           Installing packages (log: backend/data/pip-install.log)..."
  if ! "$venv_python" -m pip install -r "$ROOT/backend/requirements.txt" --disable-pip-version-check >"$pip_log" 2>&1; then
    report_pip_failure "$pip_log" "$venv_python"
    return 1
  fi
  ok "Backend dependencies installed"

  # Always run: npm install is a no-op when node_modules already matches the
  # lockfile, and picks up packages added by a git pull when it doesn't.
  echo "  [4/7] Frontend dependencies..."
  ( cd "$ROOT/frontend" && npm install --no-fund --no-audit --loglevel=error ) || { err "npm install failed in frontend"; return 1; }
  ok "Frontend dependencies installed"

  echo "  [5/7] Electron dependencies..."
  ( cd "$ROOT/frontend/electron" && npm install --no-fund --no-audit --loglevel=error ) || { err "npm install failed in frontend/electron"; return 1; }
  ensure_electron_binary || return 1
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
    echo "  [ --]   Claude Code CLI not found - https://claude.com/product/claude-code"
  fi
  if command -v gh >/dev/null 2>&1; then
    ok "GitHub CLI detected - GitHub actions enabled"; found_any=1
  else
    echo "  [ --]   GitHub CLI not found - https://cli.github.com"
  fi
  if command -v git >/dev/null 2>&1; then
    ok "Git detected - repository-aware actions enabled"
  else
    echo "  [ --]   Git not found - repo detection falls back to a default folder"
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

MACOS_APP_DIR="${HOME}/Applications"
MACOS_APP_PATH="${MACOS_APP_DIR}/VDock.app"

# Builds ~/Applications/VDock.icns from the repo's 1024px icon.
build_macos_icon() {
  local icon_source="$ROOT/frontend/public/vdock-icon.png"
  local output_icns="$1"
  local iconset_dir
  iconset_dir="$(mktemp -d)/VDock.iconset"
  mkdir -p "$iconset_dir"

  [[ -f "$icon_source" ]] || return 1

  local base_size
  for base_size in 16 32 128 256 512; do
    sips -z "$base_size" "$base_size" "$icon_source" \
      --out "$iconset_dir/icon_${base_size}x${base_size}.png" >/dev/null 2>&1 || return 1
    sips -z "$((base_size * 2))" "$((base_size * 2))" "$icon_source" \
      --out "$iconset_dir/icon_${base_size}x${base_size}@2x.png" >/dev/null 2>&1 || return 1
  done

  iconutil -c icns "$iconset_dir" -o "$output_icns" >/dev/null 2>&1
}

# Apps opened from Finder/Launchpad get a bare PATH (/usr/bin:/bin:...), so
# Node or Python installed by mise, nvm, volta, asdf or Homebrew would be
# "not found". The generated launcher therefore (1) asks the user's own login
# shell for its PATH at run time, and (2) falls back to the tool folders found
# during setup, so it keeps working even if the shell cannot be queried.
write_macos_app_launcher() {
  local launcher_path="$1"
  local setup_tool_dirs=""
  local tool_name tool_path

  for tool_name in node npm python3; do
    tool_path="$(command -v "$tool_name" 2>/dev/null || true)"
    [[ -n "$tool_path" ]] || continue

    local tool_dir
    tool_dir="$(dirname "$tool_path")"
    case ":$setup_tool_dirs:" in
      *":$tool_dir:"*) ;;
      *) setup_tool_dirs="${setup_tool_dirs:+$setup_tool_dirs:}$tool_dir" ;;
    esac
  done

  local launcher_template
  launcher_template="$(cat << 'LAUNCHER_EOF'
#!/bin/bash
# Generated by VDock's setup.sh - re-run ./setup.sh --shortcut to regenerate.
VDOCK_ROOT="__VDOCK_ROOT__"
SETUP_TOOL_DIRS="__SETUP_TOOL_DIRS__"
LAUNCH_LOG="$VDOCK_ROOT/backend/data/vdock-app-launch.log"

show_error() {
  osascript -e "display dialog \"$1\" with title \"VDock\" buttons {\"OK\"} default button \"OK\" with icon caution" >/dev/null 2>&1
}

# The login shell prints its PATH between markers so profile noise is ignored.
read_login_shell_path() {
  local marker="__VDOCK_PATH__"
  local shell_output
  shell_output="$("${SHELL:-/bin/zsh}" -ilc "printf '${marker}%s${marker}' \"\$PATH\"" 2>/dev/null)" || return 0
  shell_output="${shell_output#*"$marker"}"
  printf '%s' "${shell_output%%"$marker"*}"
}

if [ ! -f "$VDOCK_ROOT/launch.sh" ]; then
  show_error "VDock was moved or deleted. Run ./setup.sh from the new VDock folder to fix this shortcut."
  exit 1
fi

login_shell_path="$(read_login_shell_path)"
export PATH="${login_shell_path:+$login_shell_path:}${SETUP_TOOL_DIRS:+$SETUP_TOOL_DIRS:}$PATH"

mkdir -p "$VDOCK_ROOT/backend/data"
cd "$VDOCK_ROOT" || exit 1
export VDOCK_AUTO_CLOSE_LAUNCHER=1

if ! bash ./launch.sh >"$LAUNCH_LOG" 2>&1; then
  last_error="$(grep -E 'ERROR|WARN' "$LAUNCH_LOG" | head -n 2 | tr -d '"\\')"
  show_error "VDock could not start. ${last_error:-See the log for details.} Log: $LAUNCH_LOG"
  exit 1
fi
LAUNCHER_EOF
)"

  launcher_template="${launcher_template//__VDOCK_ROOT__/$ROOT}"
  launcher_template="${launcher_template//__SETUP_TOOL_DIRS__/$setup_tool_dirs}"
  printf '%s\n' "$launcher_template" > "$launcher_path"
}

# A real .app (Launchpad, Spotlight, Dock) that just runs launch.sh from this
# checkout. LSUIElement keeps the tiny launcher itself out of the Dock; the
# VDock window is the Electron process it starts.
create_macos_app() {
  echo ""
  echo "  Creating VDock.app..."

  local staging_app
  staging_app="$(mktemp -d)/VDock.app"
  mkdir -p "$staging_app/Contents/MacOS" "$staging_app/Contents/Resources"

  cat > "$staging_app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>VDock</string>
  <key>CFBundleDisplayName</key><string>VDock</string>
  <key>CFBundleIdentifier</key><string>com.vdock.launcher</string>
  <key>CFBundleExecutable</key><string>VDock</string>
  <key>CFBundleIconFile</key><string>VDock</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>LSUIElement</key><true/>
</dict>
</plist>
EOF

  write_macos_app_launcher "$staging_app/Contents/MacOS/VDock"
  chmod +x "$staging_app/Contents/MacOS/VDock"

  if ! build_macos_icon "$staging_app/Contents/Resources/VDock.icns"; then
    warn "Could not build the app icon (VDock.app will use a generic one)"
  fi

  mkdir -p "$MACOS_APP_DIR"
  rm -rf "$MACOS_APP_PATH"
  mv "$staging_app" "$MACOS_APP_PATH" || { warn "Could not create $MACOS_APP_PATH"; return 1; }
  touch "$MACOS_APP_PATH"
  ok "VDock.app installed in $MACOS_APP_DIR (find it in Launchpad or Spotlight)"
}

create_desktop_launcher() {
  if [[ "$(uname -s)" == "Darwin" ]]; then
    create_macos_app
    # Older setups left a VDock.command on the Desktop; the app replaces it.
    rm -f "${HOME}/Desktop/VDock.command"
    return 0
  fi

  echo ""
  echo "  Creating desktop launcher..."

  local desktop_dir="${HOME}/Desktop"

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
  clear 2>/dev/null || true
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
    echo "    - Open VDock from Launchpad or Spotlight (it is in ~/Applications)"
  fi
  echo "    - Or run: ./launch.sh"
  echo ""
  echo "  VDock opens at: http://localhost:${BACKEND_PORT:-5000}"
  echo ""
  echo "  Phone or tablet: mobile access is OFF by default, so your phone can't"
  echo "  open VDock yet. To use it: Settings > Devices & network > turn on"
  echo "  \"Allow LAN access\", relaunch VDock, then scan the QR code."
  echo ""
  read -r -p "  Start VDock now? [Y/n]: " start_now || start_now="n"
  if is_yes_answer "$start_now"; then
    launch_vdock
  fi
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

# backend/tests/test_dl010_*.py source this file for its functions only.
if [[ "${VDOCK_SETUP_LIB_ONLY:-}" == "1" ]]; then
  return 0 2>/dev/null || exit 0
fi

handle_cli_flag "${1:-}"

while true; do
  show_menu
  read -r -p "  Choose an option [1-6] (Enter = 1): " menu_choice || menu_choice="6"
  menu_choice="${menu_choice:-1}"

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
