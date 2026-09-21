"""Configuration management for VDock backend."""
import os
import json
import socket
from pathlib import Path
from typing import Dict, Any, Optional


def lan_ip() -> Optional[str]:
    """Primary LAN IPv4 — the address the 'Connect a device' QR card uses.

    The UDP-connect trick picks the right interface without sending traffic;
    falls back to the hostname lookup, then None when there is no route.
    """
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(('192.168.255.255', 1))  # unroutable — no packets sent
            return probe.getsockname()[0]
        finally:
            probe.close()
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return None


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
    
    # SSL/TLS settings
    USE_SSL = os.environ.get('USE_SSL', 'False').lower() == 'true'
    SSL_CERT_PATH = os.environ.get('SSL_CERT_PATH', 'cert.pem')
    SSL_KEY_PATH = os.environ.get('SSL_KEY_PATH', 'key.pem')
    
    
    # Data storage
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = Path(os.environ.get('DATA_DIR', str(BASE_DIR / 'data')))
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
            ip = lan_ip()
            if ip:
                origins.add(f'http://{ip}:{cls.PORT}')
                origins.add(f'http://{ip}:{frontend_port}')
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

