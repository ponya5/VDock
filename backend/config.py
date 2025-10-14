"""Configuration management for VDock backend."""
import os
import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """Application configuration."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Server settings
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Security settings
    REQUIRE_AUTH = os.environ.get('REQUIRE_AUTH', 'False').lower() == 'true'
    AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD', '')
    TOKEN_EXPIRATION = int(os.environ.get('TOKEN_EXPIRATION', 86400))  # 24 hours
    
    # Network settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001').split(',')
    ALLOW_LAN = os.environ.get('ALLOW_LAN', 'False').lower() == 'true'
    
    # SSL/TLS settings
    USE_SSL = os.environ.get('USE_SSL', 'False').lower() == 'true'
    SSL_CERT_PATH = os.environ.get('SSL_CERT_PATH', 'cert.pem')
    SSL_KEY_PATH = os.environ.get('SSL_KEY_PATH', 'key.pem')
    
    
    # Data storage
    DATA_DIR = Path(os.environ.get('DATA_DIR', 'data'))
    PROFILES_DIR = DATA_DIR / 'profiles'
    UPLOADS_DIR = DATA_DIR / 'uploads'
    PLUGINS_DIR = DATA_DIR / 'plugins'
    
    # Plugin settings
    ENABLE_PLUGINS = os.environ.get('ENABLE_PLUGINS', 'True').lower() == 'true'
    
    # Command execution settings
    REQUIRE_COMMAND_CONFIRMATION = os.environ.get('REQUIRE_COMMAND_CONFIRMATION', 'True').lower() == 'true'
    ALLOWED_COMMAND_PATTERNS = []
    
    @classmethod
    def init_app(cls):
        """Initialize application directories and configuration."""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.PROFILES_DIR.mkdir(exist_ok=True)
        cls.UPLOADS_DIR.mkdir(exist_ok=True)
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

