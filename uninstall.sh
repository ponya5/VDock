#!/usr/bin/env bash
# ============================================================
#  VDock Uninstall — source checkout
#  Stops running VDock processes, removes the autostart entry
#  and desktop launcher. The folder itself is deleted by hand
#  at the end; everything else lives inside it.
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS="$(uname -s)"

confirm() {
    [ "${1:-}" = "--yes" ] && return 0
    cat <<EOF

  ========================================================
    VDock Uninstall
  ========================================================

    This will:
      - Stop running VDock processes (launcher, backend,
        Vite dev server, Electron)
      - Remove the login autostart entry (if set)
      - Remove the Desktop launcher (if present)

    It does NOT delete this folder. Afterwards, delete
      $ROOT
    to remove VDock completely — profiles and settings in
    backend/data go with it.

EOF
    local reply
    read -r -p "  Continue? [y/N]: " reply
    [[ "$reply" =~ ^[Yy]$ ]]
}

stop_processes() {
    echo ""
    echo "  [1/3] Stopping VDock processes..."

    local killed=0

    # Anything whose command line lives inside this folder (venv
    # python, vite.js, electron binary) or names the launcher —
    # it starts VDock-Launcher.py with a relative path. $$/PPID
    # guard: this script's own cmdline contains $ROOT.
    local pid
    while IFS= read -r pid; do
        [ -n "$pid" ] || continue
        kill "$pid" 2>/dev/null && killed=$((killed + 1)) || true
    done < <(pgrep -f "$ROOT" 2>/dev/null | grep -vx -e "$$" -e "$PPID" || true)

    while IFS= read -r pid; do
        [ -n "$pid" ] || continue
        kill "$pid" 2>/dev/null && killed=$((killed + 1)) || true
    done < <(pgrep -f 'VDock-Launcher\.py|vdock-backend' 2>/dev/null | grep -vx -e "$$" -e "$PPID" || true)

    if [ "$killed" -gt 0 ]; then
        echo "  [OK]    Stopped $killed process(es)"
    else
        echo "  [ --]   No VDock processes running"
    fi
}

remove_autostart() {
    echo ""
    echo "  [2/3] Removing autostart entry..."

    if [ "$OS" = "Darwin" ]; then
        local plist="$HOME/Library/LaunchAgents/com.vdock.launcher.plist"
        if [ -f "$plist" ]; then
            launchctl unload "$plist" 2>/dev/null || true
            rm -f "$plist"
            echo "  [OK]    Removed $plist"
        else
            echo "  [ --]   No LaunchAgent found"
        fi
    else
        local entry="$HOME/.config/autostart/vdock.desktop"
        if [ -f "$entry" ]; then
            rm -f "$entry"
            echo "  [OK]    Removed $entry"
        else
            echo "  [ --]   No autostart entry found"
        fi
    fi
}

remove_launcher() {
    echo ""
    echo "  [3/3] Removing desktop launcher..."

    local desktop="$HOME/Desktop"
    if [ "$OS" != "Darwin" ] && [ -f "$HOME/.config/user-dirs.dirs" ]; then
        # shellcheck disable=SC1091
        local xdg_dir
        xdg_dir="$(grep '^XDG_DESKTOP_DIR=' "$HOME/.config/user-dirs.dirs" | cut -d'"' -f2 || true)"
        [ -n "$xdg_dir" ] && desktop="${xdg_dir/#\$HOME/$HOME}"
    fi

    local found=0 name
    for name in VDock.command VDock.sh vdock.desktop; do
        if [ -f "$desktop/$name" ]; then
            rm -f "$desktop/$name"
            echo "  [OK]    Removed $desktop/$name"
            found=1
        fi
    done
    [ "$found" -eq 0 ] && echo "  [ --]   No desktop launcher found"
}

main() {
    confirm "${1:-}" || { echo "  Aborted."; exit 0; }

    stop_processes
    remove_autostart
    remove_launcher

    cat <<EOF

  ========================================================
    Done. To finish removing VDock, delete this folder:
      $ROOT
  ========================================================

EOF
}

main "$@"
