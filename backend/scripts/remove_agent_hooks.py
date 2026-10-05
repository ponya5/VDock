"""Remove VDock's agent hook from every supported agent (DL-148).

uninstall.bat / uninstall.sh run this before deleting the venv, so a removed
VDock leaves no hook behind in Claude Code, Cursor, Antigravity or Codex.
Only VDock's own entries are touched (see ``agent_hooks.uninstall_hook``).

Run from anywhere:

    python backend/scripts/remove_agent_hooks.py

Always exits 0 — a settings file that can't be read is reported, never fatal,
so it can't block the rest of the uninstall.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.agent_hooks import (  # noqa: E402
    SUPPORTED_AGENTS, HookSettingsError, uninstall_hook,
)


def main() -> int:
    removed_any = False
    for agent in SUPPORTED_AGENTS:
        try:
            result = uninstall_hook(agent)
        except (HookSettingsError, OSError) as error:
            print(f'  [WARN]  {agent}: hook not removed ({error})')
            continue
        if result.removed:
            removed_any = True
            print(f'  [OK]    Removed VDock hook from {result.settings_path}')
    if not removed_any:
        print('  [ --]   No agent hooks installed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
