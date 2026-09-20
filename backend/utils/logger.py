"""Logging configuration."""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# DL-029: file logging must stay bounded — each log file rotates at
# maxBytes and keeps `backupCount` archives, so a logger caps at
# maxBytes * (1 + backupCount) instead of growing forever.
LOG_MAX_BYTES = 512 * 1024
LOG_BACKUP_COUNT = 3


def setup_logger(name: str = 'vdock', level: int = logging.INFO, log_file: Path = None) -> logging.Logger:
    """Set up application logger.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file to log to
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified — rotating so logs can't grow unbounded.
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
    
    return logger

