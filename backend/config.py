"""Configuration management for VDock backend."""
import os
import json
import logging
import re
import secrets
import shutil
import socket
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.atomic import atomic_write_text

logger = logging.getLogger('vdock.config')


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


def env_file() -> Path:
    """The one .env file VDock reads and writes.

    ``backend/.env`` for source runs; ``DATA_DIR/.env`` when frozen (the
    install directory may be read-only).
    """
    if getattr(sys, 'frozen', False):
        data_dir = os.environ.get('DATA_DIR') or str(_default_data_dir(Path(__file__).resolve().parent))
        return Path(data_dir) / '.env'
    return backend_dir() / '.env'


def migrate_legacy_env() -> bool:
    """Frozen builds: copy an install-dir ``.env`` (cwd) to ``env_file()`` once.

    Older installs kept ``.env`` next to the exe. Never overwrites an existing
    target and never logs file contents. Returns True when a copy was made.
    """
    if not getattr(sys, 'frozen', False):
        return False
    target = env_file()
    legacy = Path.cwd() / '.env'
    if target.exists() or not legacy.is_file():
        return False
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(legacy, target)
    except OSError as exc:
        logger.warning('Could not migrate .env (%s)', exc.__class__.__name__)
        return False
    logger.info('Migrated .env to %s', target)
    return True


def _load_env_file() -> None:
    """Populate os.environ from .env before ``Config`` reads it.

    ``Config``'s class attributes are evaluated once, when this module is
    first imported. app.py imports ``config`` (for ``env_file``) *before* its
    own ``load_dotenv`` runs, so every .env value — AUTH_PASSWORD included —
    was invisible to ``Config``; with ``require_auth`` saved as true the
    startup guard then refused to boot. Real environment variables still win.
    """
    try:
        from dotenv import load_dotenv
        migrate_legacy_env()  # frozen installs: copy the old .env first
        load_dotenv(env_file(), override=False)
    except Exception as exc:  # never block startup on an unreadable .env
        logger.warning('Could not read .env (%s)', exc.__class__.__name__)


_load_env_file()


# Public strings that shipped in older .env.example files. A key equal to one
# of these is readable on GitHub, so it is as good as no key at all.
KNOWN_PLACEHOLDER_SECRETS = frozenset({
    'your-secret-key-here-change-this-to-random-string',
    'your-secret-key-here-change-this-in-production',
    'your-secret-key-here',
})


#: Example passwords that shipped in templates; never valid with auth on.
EXAMPLE_PASSWORDS = frozenset({
    'ChangeThisToAStrongPassword123!', 'your-secure-password-here', 'admin',
})

LOOPBACK_HOSTS = ('127.0.0.1', 'localhost', '::1')


def is_weak_secret_key(key: Optional[str]) -> bool:
    """True for an empty, published-placeholder or too-short signing key."""
    return not key or key in KNOWN_PLACEHOLDER_SECRETS or len(key) < 32


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

    atomic_write_text(env_file, '\n'.join(out) + '\n')


def set_env_key(path: Path, key: str, value: Optional[str]) -> None:
    """Set (or, when ``value`` is None, remove) one ``KEY=value`` line.

    Byte-level and atomic: other lines, comments, order, BOM and newline style
    are preserved; only the named key's line changes. Creates the file when it
    does not exist. Never logs the value.
    """
    path = Path(path)
    raw = path.read_bytes() if path.exists() else b''
    bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    text = raw[len(bom):].decode('utf-8', errors='surrogateescape')
    newline = '\r\n' if '\r\n' in text else '\n'
    lines = text.splitlines()

    out: List[str] = []
    done = False
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith(f'{key.upper()}='):
            if value is not None and not done:
                out.append(f'{key}={value}')
            done = True
            continue
        out.append(line)
    if value is not None and not done:
        out.append(f'{key}={value}')

    body = newline.join(out) + (newline if out else '')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    try:
        tmp.write_bytes(bom + body.encode('utf-8', errors='surrogateescape'))
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


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
    def ensure_strong_secret_key(cls) -> bool:
        """Replace a missing/placeholder SECRET_KEY with a generated one.

        The new key is saved to ``env_file()`` so issued tokens survive
        restarts. Returns True when a key was generated. Never logs the key.
        """
        if not is_weak_secret_key(os.environ.get('SECRET_KEY')):
            return False
        new_key = secrets.token_hex(32)
        cls.SECRET_KEY = new_key
        os.environ['SECRET_KEY'] = new_key
        target = env_file()
        try:
            write_env_keys(target, {'SECRET_KEY': new_key})
            logger.info('Generated a new SECRET_KEY and saved it to %s', target.name)
        except OSError as exc:
            logger.warning(
                'Generated a SECRET_KEY but could not save it (%s); '
                'deck tokens will not survive a restart.', exc.__class__.__name__
            )
        return True

    @classmethod
    def validate(cls) -> None:
        """Refuse to start in a configuration that is quietly insecure.

        Raises:
            RuntimeError: authentication is on but no password is set (or it
                is a published example), DEBUG is combined with a LAN bind, or
                SSL is on without its certificate files.
        """
        if cls.REQUIRE_AUTH and not cls.AUTH_PASSWORD:
            raise RuntimeError(
                'REQUIRE_AUTH is enabled but AUTH_PASSWORD is not set. '
                'Set AUTH_PASSWORD in backend/.env, or disable REQUIRE_AUTH.'
            )
        if cls.REQUIRE_AUTH and cls.AUTH_PASSWORD in EXAMPLE_PASSWORDS:
            raise RuntimeError(
                'AUTH_PASSWORD is still an example value from .env.example. '
                f'Choose your own in {env_file()} (or Settings > Devices & network), '
                'or disable REQUIRE_AUTH.'
            )
        if cls.DEBUG and (cls.ALLOW_LAN or cls.HOST not in LOOPBACK_HOSTS):
            raise RuntimeError(
                'DEBUG exposes the Werkzeug debugger to your network. '
                f'Set DEBUG=False in {env_file()} or turn off Allow LAN.'
            )
        if cls.USE_SSL:
            for label, value in (('SSL_CERT_PATH', cls.SSL_CERT_PATH), ('SSL_KEY_PATH', cls.SSL_KEY_PATH)):
                if not Path(value).is_file():
                    raise RuntimeError(
                        f'USE_SSL is enabled but {label} points to a missing file: {value}'
                    )

    @classmethod
    def lan_without_password(cls) -> bool:
        return bool(cls.ALLOW_LAN and not (cls.REQUIRE_AUTH and cls.AUTH_PASSWORD))

    @classmethod
    def report(cls) -> List[str]:
        """Human-readable startup summary. Names and booleans only -- no values."""
        from services import integration_status

        lan = 'LAN on' if cls.ALLOW_LAN else 'LAN off'
        bind_host = cls.HOST if cls.ALLOW_LAN else '127.0.0.1'
        if cls.ALLOW_LAN and bind_host in LOOPBACK_HOSTS:
            bind_host = '0.0.0.0'
        lines = [
            f'Bind: {bind_host}:{cls.PORT} ({lan})',
            f"Auth: {'on' if cls.REQUIRE_AUTH else 'off'}",
        ]
        marks = []
        short = {'GITHUB_TOKEN': 'GitHub token', 'ANTHROPIC_API_KEY': 'Anthropic key',
                 'WEATHERAPI_KEY': 'Weather key', 'gh_cli': 'gh CLI', 'claude_cli': 'Claude CLI'}
        for item in integration_status.secret_items() + integration_status.cli_items():
            marks.append(f"{short.get(item['id'], item['label'])} {'✓' if item['configured'] else '✗'}")
        lines.append('Integrations: ' + ', '.join(marks))
        for line in lines:
            logger.info(line)
        if cls.lan_without_password():
            logger.warning(
                'Allow LAN is on without a deck password - anyone on this network '
                'can press your keys. Set one in Settings > Devices & network.'
            )
        return lines

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
        # With USE_SSL the browser's Origin is https:// - an http-only list
        # would refuse every socket and the deck would sit on "Can't reach VDock".
        scheme = 'https' if cls.USE_SSL else 'http'
        for host in ('localhost', '127.0.0.1'):
            origins.add(f'{scheme}://{host}:{cls.PORT}')       # backend serves dist
            origins.add(f'http://{host}:{frontend_port}')      # vite dev
        if cls.ALLOW_LAN:
            # Whitelist every host a device may legitimately load: the
            # auto-detected NIC address AND the deck_host override — a
            # phone on http://deck.local:PORT must not lose its socket.
            for host in {lan_ip(), cls.DECK_HOST or None}:
                if host:
                    origins.add(f'{scheme}://{host}:{cls.PORT}')
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
        atomic_write_text(config_file, json.dumps(config, indent=2))

