"""Which Windows network profile the deck's LAN adapter is on (DL-154).

Windows labels each network Public / Private / Domain. "Public" is what cafes,
hotels and unconfigured home Wi-Fi get; it is the signal that other people may
share the network, so the Connect page warns about it. macOS and Linux have no
equivalent, so they answer ``unknown``.
"""
import json
import subprocess
import time
from typing import List, Optional, Tuple

from config import _iface_candidates, lan_ip
from utils.host_os import host_os

_CACHE_TTL_S = 30
_TIMEOUT_S = 4
_cache: Tuple[float, str] = (0.0, 'unknown')

_PS_COMMAND = (
    'Get-NetConnectionProfile | '
    "Select-Object InterfaceAlias, @{n='Category';e={[string]$_.NetworkCategory}} | "
    'ConvertTo-Json -Compress'
)


def classify(category: str) -> str:
    """Map a Windows NetworkCategory to ``public | private | domain | unknown``."""
    lowered = (category or '').strip().lower()
    if lowered == 'public':
        return 'public'
    if lowered == 'private':
        return 'private'
    if lowered.startswith('domain'):
        return 'domain'
    return 'unknown'


def parse_profiles(raw: str) -> List[Tuple[str, str]]:
    """(interface alias, category) pairs from the PowerShell JSON output."""
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    return [
        (str(item.get('InterfaceAlias', '')), str(item.get('Category', '')))
        for item in data if isinstance(item, dict)
    ]


def pick_profile(profiles: List[Tuple[str, str]], iface: Optional[str]) -> str:
    """The profile of ``iface``, or ``unknown`` when no profile names it."""
    for alias, category in profiles:
        if iface and alias.lower() == iface.lower():
            return classify(category)
    return 'unknown'


def _lan_iface() -> Optional[str]:
    ip = lan_ip()
    for name, addr in _iface_candidates():
        if addr == ip:
            return name
    return None


def _query_windows() -> str:
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command', _PS_COMMAND],
            capture_output=True, text=True, timeout=_TIMEOUT_S,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
    except (OSError, subprocess.SubprocessError):
        return 'unknown'
    if result.returncode != 0:
        return 'unknown'
    return pick_profile(parse_profiles(result.stdout), _lan_iface())


def network_profile() -> str:
    """``public | private | domain | unknown`` for the LAN adapter (cached 30 s)."""
    global _cache
    if host_os() != 'windows':
        return 'unknown'
    stamp, value = _cache
    now = time.time()
    if now - stamp < _CACHE_TTL_S:
        return value
    value = _query_windows()
    _cache = (now, value)
    return value
