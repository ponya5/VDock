#!/usr/bin/env bash
# ============================================================
#  VDock Uninstall — source checkout
#  Removes everything VDock installed or generated: processes,
#  autostart entry, desktop launcher, agent hooks, Python venv,
#  node_modules, the built frontend, logs and the Electron
#  profile. Asks whether to also delete profiles and settings.
#  The source folder stays so setup.sh can reinstall from it.
#
#  Non-interactive:  ./uninstall.sh --yes             keep profiles/settings
#                    ./uninstall.sh --yes --complete  delete them too
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS="$(uname -s)"
COMPLETE=""
UNATTENDED=""
LEFTOVER=""

for arg in "$@"; do
    case "$arg" in
        --yes) UNATTENDED=1 ;;
        --complete) COMPLETE=1 ;;
    esac
done

choose_mode() {
    [ -n "$UNATTENDED" ] && return 0
    cat <<EOF

  ========================================================
    VDock Uninstall
  ========================================================

    Removes VDock from this computer: stops it, removes the
    autostart entry, desktop launcher and agent hooks, and
    deletes the installed dependencies, built frontend,
    logs and app cache.

    [1] Keep my profiles and settings (recommended)
        Running setup.sh later restores the same deck.

    [2] Complete uninstall
        Also deletes profiles, settings, uploads, themes,
        plugins and integration keys. Cannot be undone.

    [3] Cancel

EOF
    local mode confirm
    read -r -p "  Choose an option [1-3]: " mode || mode=""
    case "$mode" in
        1) return 0 ;;
        2)
            echo ""
            read -r -p "  Delete all profiles and settings too? Type YES to confirm: " confirm || confirm=""
            if [[ "$confirm" =~ ^[Yy][Ee][Ss]$ ]]; then
                COMPLETE=1
                return 0
            fi
            ;;
    esac
    return 1
}

stop_processes() {
    echo ""
    echo "  [1/6] Stopping VDock processes..."

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
        sleep 2
        echo "  [OK]    Stopped $killed process(es)"
    else
        echo "  [ --]   No VDock processes running"
    fi
}

remove_agent_hooks() {
    echo ""
    echo "  [2/6] Removing agent hooks..."
    # Runs before the venv is deleted: the remover uses the backend's
    # own hook code and only touches VDock's entries.
    local py=""
    if [ -x "$ROOT/backend/venv/bin/python" ]; then
        py="$ROOT/backend/venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        py="python3"
    fi
    if [ -z "$py" ]; then
        echo "  [ --]   Python not found - skipped agent hook removal"
        return 0
    fi
    "$py" "$ROOT/backend/scripts/remove_agent_hooks.py" \
        || echo "  [WARN]  Could not check agent hooks (needs the VDock Python venv)"
}

remove_autostart() {
    echo ""
    echo "  [3/6] Removing autostart entry..."

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
    echo "  [4/6] Removing desktop launcher..."

    local desktop="${DESKTOP_DIR:-$HOME/Desktop}"
    if [ -z "${DESKTOP_DIR:-}" ] && [ "$OS" != "Darwin" ] && [ -f "$HOME/.config/user-dirs.dirs" ]; then
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
    return 0
}

remove_dir() {
    local rel="$1" path="$2"
    [ -e "$path" ] || return 0
    rm -rf "$path" 2>/dev/null || true
    if [ -e "$path" ]; then
        echo "  [WARN]  Could not fully remove $rel"
        LEFTOVER=1
    else
        echo "  [OK]    Removed $rel"
    fi
}

remove_installed_files() {
    echo ""
    echo "  [5/6] Removing installed files..."
    local rel
    for rel in backend/venv backend/.pytest_cache frontend/node_modules \
               frontend/electron/node_modules frontend/dist frontend/.vite; do
        remove_dir "$rel" "$ROOT/$rel"
    done
    rm -f "$ROOT"/frontend/*.tsbuildinfo
    find "$ROOT/backend" "$ROOT/scripts" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
    rm -f "$ROOT"/backend/data/*.log "$ROOT"/backend/data/*.log.* "$ROOT/backend/data/now_playing_art.bin"
    echo "  [OK]    Removed caches and logs"

    # The VDock window's Electron profile: HTTP + service-worker caches
    # (which can keep serving an old frontend), local storage, GPU caches.
    local electron_profile
    if [ "$OS" = "Darwin" ]; then
        electron_profile="$HOME/Library/Application Support/vdock-electron"
    else
        electron_profile="${XDG_CONFIG_HOME:-$HOME/.config}/vdock-electron"
    fi
    remove_dir "app cache $electron_profile" "$electron_profile"
}

remove_user_data() {
    echo ""
    echo "  [6/6] Profiles and settings..."
    if [ -z "$COMPLETE" ]; then
        echo "  [OK]    Kept profiles, settings and integration keys"
        echo "          (backend/data, backend/.env, frontend/.env)"
        return 0
    fi
    rm -f "$ROOT/backend/.env" "$ROOT/frontend/.env"
    # Delete everything in backend/data except the files that ship with
    # VDock (config.example.json, templates/, the .gitkeep placeholders),
    # so the checkout is left exactly as cloned.
    local data="$ROOT/backend/data" item
    if [ -d "$data" ]; then
        shopt -s dotglob nullglob
        for item in "$data"/*; do
            case "$(basename "$item")" in
                config.example.json|templates) continue ;;
            esac
            if [ -d "$item" ]; then
                find "$item" -mindepth 1 -maxdepth 1 ! -name .gitkeep -exec rm -rf {} +
            else
                rm -f "$item"
            fi
        done
        shopt -u dotglob nullglob
    fi
    echo "  [OK]    Deleted profiles, settings, uploads and integration keys"
}

main() {
    choose_mode || { echo "  Aborted. Nothing was changed."; exit 0; }

    stop_processes
    remove_agent_hooks
    remove_autostart
    remove_launcher
    remove_installed_files
    remove_user_data

    echo ""
    echo "  ========================================================"
    echo "    VDock is uninstalled."
    if [ -n "$LEFTOVER" ]; then
        echo "    Some files were in use - close any VDock or editor"
        echo "    windows and run ./uninstall.sh again to finish."
    fi
    echo ""
    echo "    To reinstall fresh: run ./setup.sh"
    echo "    To remove VDock for good: delete this folder:"
    echo "      $ROOT"
    echo "  ========================================================"
    echo ""
}

main
