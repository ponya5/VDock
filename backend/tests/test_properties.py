from hypothesis import given, settings, strategies as st, HealthCheck
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.file_manager import FileManager
from app import app
from config import Config

# Feature: app-cleanup-and-improvements, Property 3: FileManager logs errors via logger

@given(method=st.sampled_from(['save_json', 'load_json', 'delete_file', 'copy_file', 'list_files']))
@settings(max_examples=100, deadline=None, suppress_health_check=list(HealthCheck))
def test_file_manager_uses_logger(method, tmp_path, mocker):
    mock_logger = mocker.patch('utils.file_manager.logger')
    
    if method == 'save_json':
        mocker.patch('utils.file_manager.json.dump', side_effect=OSError("Mock Error"))
        FileManager.save_json(tmp_path / "test.json", {"test": 1})
    elif method == 'load_json':
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")
        mocker.patch('utils.file_manager.open', side_effect=OSError("Mock Error"))
        FileManager.load_json(test_file)
    elif method == 'delete_file':
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")
        mocker.patch.object(Path, 'unlink', side_effect=OSError("Mock Error"))
        FileManager.delete_file(test_file)
    elif method == 'copy_file':
        mocker.patch('utils.file_manager.shutil.copy2', side_effect=OSError("Mock Error"))
        FileManager.copy_file(tmp_path / "src", tmp_path / "dst")
    elif method == 'list_files':
        mocker.patch.object(Path, 'glob', side_effect=OSError("Mock Error"))
        FileManager.list_files(tmp_path, "*.json")

    assert mock_logger.error.called


# Feature: app-cleanup-and-improvements, Property 2: profile routes require auth

@given(route=st.sampled_from(['/api/profiles', '/api/profiles/123']), method=st.sampled_from(['GET', 'POST', 'PUT']))
@settings(max_examples=20, deadline=None)  # 20 is enough for routing
def test_profile_routes_require_auth(route, method):
    # Enable auth
    Config.REQUIRE_AUTH = True
    
    valid_methods = {
        '/api/profiles': ['GET', 'POST'],
        '/api/profiles/123': ['GET', 'PUT']
    }
    
    if method not in valid_methods.get(route, []):
        return
        
    with app.test_client() as c:
        resp = getattr(c, method.lower())(route)
        assert resp.status_code in (401, 403)
