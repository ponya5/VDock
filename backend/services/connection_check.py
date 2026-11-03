"""\"Why can't my phone connect?\" (DL-160).

Read-only diagnosis of the things that make a scanned QR show nothing: Allow
LAN off / restart pending, a saved address override that is not this
computer, a firewall, and the server not answering on the QR address.

Each check is ``{id, status, title, detail, fix?}`` with ``status`` one of
``ok | warn | fail | info``. ``fix`` is ``{action, label, value?}`` — the UI
runs it through the existing ``PUT /api/config {deck_host}``; this module
never changes anything.

Probes (_local_ips, _resolve, _http_ok, _firewall_on, _computer_name) are
module seams so tests need no network.
"""
import ipaddress
import socket
import ssl
import subprocess
import urllib.request
from typing import Any, Dict, List, Optional

from config import Config, _iface_candidates, lan_ip
from services.network_profile import network_profile
from utils.host_os import host_os


def _local_ips() -> List[str]:
    return sorted({ip for _, ip in _iface_candidates()})


def _resolve(host: str) -> Optional[str]:
    try:
        return socket.gethostbyname(host)
    except OSError:
        return None


def _http_ok(url: str) -> bool:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # self-signed deck cert; this only asks "is anyone home"
    try:
        with urllib.request.urlopen(url, timeout=3, context=ctx) as resp:  # noqa: S310
            return resp.status == 200
    except Exception:
        return False


def _firewall_on() -> Optional[bool]:
    """macOS application firewall state; None when unknown / not macOS."""
    if host_os() != 'macos':
        return None
    try:
        out = subprocess.run(
            ['/usr/libexec/ApplicationFirewall/socketfilterfw', '--getglobalstate'],
            capture_output=True, text=True, timeout=3,
        ).stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return None
    return 'enabled' in out


def _computer_name() -> Optional[str]:
    """A name other devices can resolve: macOS ``<LocalHostName>.local``."""
    if host_os() == 'macos':
        try:
            name = subprocess.run(['scutil', '--get', 'LocalHostName'],
                                  capture_output=True, text=True, timeout=3).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
        return f'{name}.local' if name else None
    name = socket.gethostname().split('.')[0]
    return name or None


def _check(id_: str, status: str, title: str, detail: str,
           fix: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    item: Dict[str, Any] = {'id': id_, 'status': status, 'title': title, 'detail': detail}
    if fix:
        item['fix'] = fix
    return item


def _is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _lan_check() -> Dict[str, Any]:
    if not Config.ALLOW_LAN:
        return _check('lan', 'fail', 'Phone & tablet access is off',
                      'Turn on "Allow phone & tablet access" under Network & ports, then restart VDock.')
    if Config.restart_required():
        return _check('lan', 'fail', 'Restart needed',
                      'Phone access was changed but VDock is still listening only on this computer. Restart VDock.')
    return _check('lan', 'ok', 'Phone access is on', 'VDock listens on your network.')


def _address_check(host: Optional[str], override: str, local: List[str]) -> Dict[str, Any]:
    if not host:
        return _check('address', 'fail', 'No network address found',
                      'This computer has no network address. Connect it to Wi-Fi or Ethernet.')
    if not override:
        if local and host not in local:
            return _check('address', 'warn', f'QR address {host}',
                          'It is not one of this computer\'s addresses right now.')
        return _check('address', 'ok', f'QR address {host}', 'Detected automatically from this computer\'s network.')
    fix = {'action': 'clear_deck_host', 'label': 'Clear the override'}
    if _is_ip(override):
        if override in local:
            return _check('address', 'ok', f'QR address {override}', 'Saved override; it matches this computer.')
        mine = ', '.join(local) or 'none found'
        return _check('address', 'fail', f'Saved address {override} is not this computer',
                      f'The QR points at {override}, but this computer is {mine}. '
                      'A phone can never reach it — usually left over from another network.', fix)
    resolved = _resolve(override)
    if resolved and (resolved in local or resolved.startswith('127.')):
        return _check('address', 'ok', f'QR address {override}', f'Saved name; it resolves to this computer ({resolved}).')
    return _check('address', 'warn', f'Saved name {override} does not resolve here',
                  'This computer cannot resolve the name itself, so a phone may not either.', fix)


def run_checks() -> List[Dict[str, Any]]:
    local = _local_ips()
    override = (Config.DECK_HOST or '').strip()
    host = override or lan_ip()
    checks = [_lan_check(), _address_check(host, override, local)]

    if host and checks[0]['status'] == 'ok':
        scheme = 'https' if Config.USE_SSL else 'http'
        if _http_ok(f'{scheme}://{host}:{Config.PORT}/api/health'):
            checks.append(_check('reachable', 'ok', 'VDock answers on that address',
                                 f'{scheme}://{host}:{Config.PORT} responds from this computer.'))
        else:
            checks.append(_check('reachable', 'fail', 'VDock does not answer on that address',
                                 f'No response from {scheme}://{host}:{Config.PORT}. Check the address above and the port.'))

    if _firewall_on():
        checks.append(_check('firewall', 'warn', 'Mac firewall is on',
                             'If the phone times out, allow incoming connections for VDock '
                             '(System Settings → Network → Firewall → Options).'))
    elif network_profile() == 'public':
        checks.append(_check('firewall', 'warn', 'Windows network is "Public"',
                             'Windows blocks incoming connections on Public networks. Set the network to Private.'))

    name = _computer_name()
    if name and name.lower() != override.lower():
        checks.append(_check('hostname', 'info', f'Network-proof address: {name}',
                             'A computer name keeps working when you change Wi-Fi (home ↔ office), '
                             'so the phone stays paired. Needs a network that allows name lookup.',
                             {'action': 'set_deck_host', 'label': f'Use {name}', 'value': name}))

    if Config.REQUIRE_AUTH:
        checks.append(_check('pairing', 'info', 'Pairing is required',
                             'Scan a fresh QR: a code lasts 3 minutes, works once, and a restart of VDock invalidates unused codes.'))
    return checks
