"""File management utilities."""
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


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
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving JSON file {file_path}: {e}")
            return False
    
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
            print(f"Error loading JSON file {file_path}: {e}")
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
            print(f"Error deleting file {file_path}: {e}")
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
            print(f"Error copying file from {src} to {dst}: {e}")
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
            print(f"Error listing files in {directory}: {e}")
            return []
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            ISO formatted timestamp string
        """
        return datetime.utcnow().isoformat() + 'Z'

