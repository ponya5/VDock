"""File management utilities."""
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import date, datetime
import logging

from .atomic import atomic_write_text

logger = logging.getLogger('vdock')

PROFILE_BACKUPS_KEPT = 7


class FileManager:
    """Manages file operations for profiles and configurations."""
    
    @staticmethod
    def save_json(file_path: Path, data: Dict[str, Any]) -> bool:
        """Save data to a JSON file.
        
        Args:
            file_path: Path to save the file
            data: Data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            atomic_write_text(file_path, json.dumps(data, indent=2, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error('Error saving JSON file %s: %s', file_path, e)
            return False

    @staticmethod
    def backup_profiles(data_dir: Path) -> bool:
        """Copy ``profiles/*.json`` to ``backups/profiles-YYYYMMDD/`` once a day.

        Keeps the newest ``PROFILE_BACKUPS_KEPT`` folders. Never raises: a
        backup problem must not fail the save that triggered it. Returns True
        only when a new backup folder was written.
        """
        try:
            target = data_dir / 'backups' / f'profiles-{date.today():%Y%m%d}'
            if target.exists():
                return False
            profiles = data_dir / 'profiles'
            if not profiles.is_dir():
                return False
            target.mkdir(parents=True)
            try:
                for src in profiles.glob('*.json'):
                    shutil.copy2(src, target / src.name)
            except Exception:
                shutil.rmtree(target, ignore_errors=True)  # no half-backups
                raise
            folders = sorted(p for p in target.parent.glob('profiles-*') if p.is_dir())
            for stale in folders[:-PROFILE_BACKUPS_KEPT]:
                shutil.rmtree(stale, ignore_errors=True)
            return True
        except Exception as e:
            logger.warning('Profile backup skipped: %s', e.__class__.__name__)
            return False

    @staticmethod
    def save_profile(file_path: Path, data: Dict[str, Any]) -> bool:
        """``save_json`` for ``profiles/*.json``: takes the daily backup first."""
        FileManager.backup_profiles(file_path.parent.parent)
        return FileManager.save_json(file_path, data)
    
    @staticmethod
    def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
        """Load data from a JSON file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Loaded data or None if error
        """
        try:
            if not file_path.exists():
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error('Error loading JSON file %s: %s', file_path, e)
            return None
    
    @staticmethod
    def delete_file(file_path: Path) -> bool:
        """Delete a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            logger.error('Error deleting file %s: %s', file_path, e)
            return False
    
    @staticmethod
    def copy_file(src: Path, dst: Path) -> bool:
        """Copy a file.
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error('Error copying file from %s to %s: %s', src, dst, e)
            return False
    
    @staticmethod
    def list_files(directory: Path, pattern: str = '*') -> list:
        """List files in a directory.
        
        Args:
            directory: Directory to list
            pattern: Glob pattern for filtering
            
        Returns:
            List of file paths
        """
        try:
            if not directory.exists():
                return []
            return list(directory.glob(pattern))
        except Exception as e:
            logger.error('Error listing files in %s: %s', directory, e)
            return []
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            ISO formatted timestamp string
        """
        return datetime.utcnow().isoformat() + 'Z'

