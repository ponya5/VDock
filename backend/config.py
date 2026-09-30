"""Configuration management for VDock backend."""
import os
import json
import re
import socket
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def _default_data_dir(base_dir: Path) -> Path:
    """Where runtime data lives when DATA_DIR is not set.

    Dev/source runs keep ``backend/data`` next to the code. A frozen
    (PyInstaller) binary can land inside Program Files or another
    read-only location, so it writes to the per-user app-data dir instead.
    """
    if not getattr(sys, 'frozen', False):
        return base_dir / 'data'
    if sys.platform == 'win32':
        root = os.environ.get('APPDATA') or str(Path.home() / 'AppData' / 'Roaming')
        return Path(root) / 'VDock'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'VDock'
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))) / 'vdock'


def _probe_ip() -> Optional[str]:
    """IPv4 of the interface the default route would use.

    UDP-connect trick — no packets are actually sent; the kernel just
    reports which source address it would pick for the target.
    """
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(('192.168.255.255', 1))  # unroutable
            return probe.getsockname()[0]
        finally:
            probe.close()
    except OSError:
        return None


# Interface-name fragments that can never serve a device on the physical
# LAN: VM/container bridges, VPN/overlay tunnels, loopback adapters.
# When a VPN captures the default route the probe lands on one of these.
_VIRTUAL_IFACE_HINTS = (
    'vethernet', 'hyper-v', 'wsl', 'vmware', 'virtualbox', 'loopback',
    'bluetooth', 'tailscale', 'zerotier', 'wireguard', '_wg_', 'wg-',
    'openvpn', 'wintun', 'tap-', 'vpn', 'tunnel', 'docker', 'br-',
)


def _iface_candidates() -> List[Tuple[str, str]]:
    """(interface name, IPv4) for every up interface — loopback and
    link-local addresses excluded."""
    try:
        import psutil
        stats = psutil.net_if_stats()
        out: List[Tuple[str, str]] = []
        for iface, addrs in psutil.net_if_addrs().items():
            st = stats.get(iface)
            if not st or not st.isup:
                continue
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    if not ip.startswith(('127.', '169.254.')):
                        out.append((iface, ip))
        return out
    except Exception:
        return []


def _lan_rank(ip: str) -> int:
    """Preference order for a physical-LAN guess: the classic home-LAN
    class first, then 10/8, then 172.16/12, then anything else."""
    if ip.startswith('192.168.'):
        return 0
    if ip.startswith('10.'):
        return 1
    if ip.startswith('172.'):
        try:
            return 2 if 16 <= int(ip.split('.')[1]) <= 31 else 3
        except (IndexError, ValueError):
            return 3
    return 3


def lan_ip() -> Optional[str]:
    """Primary LAN IPv4 — the address the 'Connect a device' QR card uses.

    The UDP probe answers "which interface would the default route use" —
    but a VPN/overlay adapter can capture that route, which advertises an
    address a phone on Wi-Fi cannot reach. So when the probe lands on a
    virtual interface, pick the best physical adapter instead (DL-056
    follow-up).
    """
    probe_ip = _probe_ip()
    reals = [(name, ip) for name, ip in _iface_candidates()
             if not any(h in name.lower() for h in _VIRTUAL_IFACE_HINTS)]
    if probe_ip and any(ip == probe_ip for _, ip in reals):
        return probe_ip
    if reals:
        return sorted(reals, key=lambda item: _lan_rank(item[1]))[0][1]
    if probe_ip:
        # Every interface is virtual/overlay — e.g. a Tailscale-only box;
        # a device on the same overlay can still reach the probe address.
        return probe_ip
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return None


# Bare hostname or IPv4 — the 'Connect a device' deck-address override.
# No scheme, port, path, or whitespace; the port shown is the real bind
# port, so a value like 'http://host:4444' must be rejected, not carried.
DECK_HOST_RE = re.compile(r'^[A-Za-z0-9]([A-Za-z0-9.\-]{0,251}[A-Za-z0-9])?$')


def _read_env_port(env_file: Path, key: str, default: int) -> int:
    """Pull a PORT-style value out of a .env file (same parse as the launcher)."""
    try:
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith(f'{key}='):
                return int(line.split('=', 1)[1].strip())
    except (OSError, ValueError):
        pass
    return default


# Shared .env helpers — routes that persist launch-time configuration
# (ports, auth password) write through these so comments, blank lines and
# unrelated keys survive the rewrite.

def project_root() -> Path:
    return Path(__file__).parent.parent.absolute()


def backend_dir() -> Path:
    return project_root() / 'backend'


def read_env_key(env_file: Path, key: str) -> str:
    """Return the value of ``KEY`` in a .env file ('' when absent)."""
    if not env_file.exists():
        return ''
    try:
        for line in env_file.read_text().splitlines():
            stripped = line.strip()
            if stripped.upper().startswith(f'{key.upper()}='):
                return stripped.split('=', 1)[1].strip()
    except OSError:
        pass
    return ''


def write_env_keys(env_file: Path, updates: Dict[str, str]) -> None:
    """Replace ``KEY=value`` lines in place; append keys that are missing.

    Preserves comments, blank lines and unrelated keys.
    """
    env_file.parent.mkdir(parents=True, exist_ok=True)
    lines = env_file.read_text().splitlines() if env_file.exists() else []

    remaining = dict(updates)
    out = []
    for line in lines:
        replaced = False
        for key in list(remaining):
            if line.strip().upper().startswith(f'{key.upper()}='):
                out.append(f'{key}={remaining.pop(key)}')
                replaced = True
                break
        if not replaced:
            out.append(line)
    for key, value in remaining.items():
        out.append(f'{key}={value}')

    env_file.write_text('\n'.join(out) + '\n')


class Config:
    """Application configuration."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Server settings
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Security settings
    REQUIRE_AUTH = os.environ.get('REQUIRE_AUTH', 'False').lower() == 'true'  # No login screen in the UI; opt in via env var
    # No default password. 'admin' as a fallback is only ever a trap: it is
    # fine while REQUIRE_AUTH is False (the default), and becomes a wide-open
    # door the moment someone turns auth on without setting a password.
    # init_app() refuses to start in that state instead.
    AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD', '')
    TOKEN_EXPIRATION = int(os.environ.get('TOKEN_EXPIRATION', 86400))  # 24 hours
    
    # Rate limiting settings
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'False').lower() == 'true'  # Disabled for local development
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100000 per hour, 10000 per minute')  # Very high limits for local use
    
    # Network settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001').split(',')
    ALLOW_LAN = os.environ.get('ALLOW_LAN', 'False').lower() == 'true'
    # 'Connect a device' address override — a bare hostname/IPv4 shown in
    # the QR card instead of the auto-detected NIC address (multi-NIC/VPN
    # boxes, or a friendly name like deck.local). Empty = auto.
    DECK_HOST = os.environ.get('DECK_HOST', '')

    # Per-app executable overrides (DL-084): { appKey: absolutePath } for
    # apps installed off-PATH — Cursor's default install is the motivating
    # case. Persisted in config.json; consumed by find_binary / open_app /
    # the keymap launch-on-missing-window retry.
    APP_PATHS = {}
    
    # SSL/TLS settings
    USE_SSL = os.environ.get('USE_SSL', 'False').lower() == 'true'
    SSL_CERT_PATH = os.environ.get('SSL_CERT_PATH', 'cert.pem')
    SSL_KEY_PATH = os.environ.get('SSL_KEY_PATH', 'key.pem')
    
    
    # Data storage
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = Path(os.environ.get('DATA_DIR', str(_default_data_dir(BASE_DIR))))
    PROFILES_DIR = DATA_DIR / 'profiles'
    UPLOADS_DIR = DATA_DIR / 'uploads'
    PLUGINS_DIR = DATA_DIR / 'plugins'
    
    # Plugin settings
    ENABLE_PLUGINS = os.environ.get('ENABLE_PLUGINS', 'True').lower() == 'true'
    
    # Command execution settings
    REQUIRE_COMMAND_CONFIRMATION = os.environ.get('REQUIRE_COMMAND_CONFIRMATION', 'True').lower() == 'true'
    ALLOW_COMMAND_EXECUTION = os.environ.get('ALLOW_COMMAND_EXECUTION', 'False').lower() == 'true'
    ALLOWED_COMMAND_PATTERNS = [
        # Only allow safe, predefined commands
        'shutdown', 'restart', 'lock', 'sleep',
        'volume_up', 'volume_down', 'volume_mute',
        'media_play_pause', 'media_next', 'media_previous', 'media_stop'
    ]
    
    # Weather API settings.
    #
    # No default key: a working credential committed to a public repo is a
    # credential leak, and this one was dead config anyway -- WeatherAction
    # reads WEATHERAPI_KEY from the environment directly, and the screensaver
    # widget uses Open-Meteo, which needs no key at all. Set this only if you
    # want the backend weather action to use weatherapi.com.
    WEATHERAPI_KEY = os.environ.get('WEATHERAPI_KEY', '')
    
    @classmethod
    def validate(cls) -> None:
        """Refuse to start in a configuration that is quietly insecure.

        Raises:
            RuntimeError: authentication is on but no password is set.
        """
        if cls.REQUIRE_AUTH and not cls.AUTH_PASSWORD:
            raise RuntimeError(
                'REQUIRE_AUTH is enabled but AUTH_PASSWORD is not set. '
                'Set AUTH_PASSWORD in backend/.env, or disable REQUIRE_AUTH.'
            )

    @classmethod
    def apply_saved_toggles(cls):
        """Re-apply persisted toggle switches over the env-derived defaults.

        PUT /api/config writes these keys to config.json and updates the
        runtime class attrs — but nothing used to read them back at startup,
        so "applies on next launch" never happened: ALLOW_LAN toggled on in
        Settings still bound 127.0.0.1 after a restart. The file is the
        source of truth once it exists; env vars only seed first run.
        """
        saved = cls.load_config()
        for key, attr in (
            ('require_auth', 'REQUIRE_AUTH'),
            ('allow_lan', 'ALLOW_LAN'),
            ('use_ssl', 'USE_SSL'),
            ('enable_plugins', 'ENABLE_PLUGINS'),
        ):
            if isinstance(saved.get(key), bool):
                setattr(cls, attr, saved[key])
        # deck_host is a string override — only DECK_HOST_RE-clean values
        # that already survived the PUT validation can land here, but a
        # hand-edited config.json gets the same check.
        saved_deck_host = saved.get('deck_host')
        if isinstance(saved_deck_host, str) and DECK_HOST_RE.fullmatch(saved_deck_host):
            cls.DECK_HOST = saved_deck_host
        # app_paths — str→str map; only clean entries that already survived
        # PUT validation can land here.
        saved_paths = saved.get('app_paths')
        if isinstance(saved_paths, dict):
            cls.APP_PATHS = {
                str(k): str(v) for k, v in saved_paths.items()
                if isinstance(v, str) and v.strip()
            }

    @classmethod
    def init_app(cls):
        """Initialize application directories and configuration."""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.PROFILES_DIR.mkdir(exist_ok=True)
        cls.UPLOADS_DIR.mkdir(exist_ok=True)
        (cls.UPLOADS_DIR / 'backgrounds').mkdir(exist_ok=True)
        (cls.UPLOADS_DIR / 'button_backgrounds').mkdir(exist_ok=True)
        cls.PLUGINS_DIR.mkdir(exist_ok=True)

        # Create default config file if it doesn't exist
        config_file = cls.DATA_DIR / 'config.json'
        if not config_file.exists():
            cls.save_config({
                'host': cls.HOST,
                'port': cls.PORT,
                'require_auth': cls.REQUIRE_AUTH,
                'allow_lan': cls.ALLOW_LAN,
                'use_ssl': cls.USE_SSL,
                'enable_plugins': cls.ENABLE_PLUGINS
            })

        # Apply saved toggles before validate() — a file-set REQUIRE_AUTH must
        # still hit the "no password set" guard.
        cls.apply_saved_toggles()
        cls.validate()
    
    @classmethod
    def socket_origins(cls):
        """Origins allowed to open a Socket.IO connection.

        The page is often served from a different origin than the socket:
        the Vite dev server proxies /api but the socket connects cross-origin
        (localhost:4444 → :5000), and ALLOW_LAN serves phones from the LAN IP.
        python-engineio rejects any Origin not in this list — including a
        same-origin one — so each real serving origin must be named.
        """
        origins = set(o.strip() for o in cls.CORS_ORIGINS if o.strip())
        frontend_port = _read_env_port(
            cls.BASE_DIR.parent / 'frontend' / '.env', 'VITE_PORT', 3000
        )
        for host in ('localhost', '127.0.0.1'):
            origins.add(f'http://{host}:{cls.PORT}')       # backend serves dist
            origins.add(f'http://{host}:{frontend_port}')  # vite dev
        if cls.ALLOW_LAN:
            # Whitelist every host a device may legitimately load: the
            # auto-detected NIC address AND the deck_host override — a
            # phone on http://deck.local:PORT must not lose its socket.
            for host in {lan_ip(), cls.DECK_HOST or None}:
                if host:
                    origins.add(f'http://{host}:{cls.PORT}')
                    origins.add(f'http://{host}:{frontend_port}')
        return sorted(origins)

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load configuration from file."""
        config_file = cls.DATA_DIR / 'config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    @classmethod
    def save_config(cls, config: Dict[str, Any]):
        """Save configuration to file."""
        config_file = cls.DATA_DIR / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

