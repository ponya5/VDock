# VDock Backend

Python Flask backend for VDock virtual stream deck application.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure:
```bash
copy .env.example .env
```

5. Run the server:
```bash
python app.py
```

## Configuration

Edit `.env` file to configure:
- `HOST`: Server host (default: 127.0.0.1)
- `PORT`: Server port (default: 5000)
- `AUTH_PASSWORD`: Password for authentication
- `ALLOW_LAN`: Allow connections from LAN (default: False)
- `USE_SSL`: Enable HTTPS (default: False)

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/verify` - Verify token

### Profiles
- `GET /api/profiles` - Get all profiles
- `GET /api/profiles/<id>` - Get specific profile
- `POST /api/profiles` - Create new profile
- `PUT /api/profiles/<id>` - Update profile
- `DELETE /api/profiles/<id>` - Delete profile
- `POST /api/profiles/<id>/duplicate` - Duplicate profile
- `GET /api/profiles/export/<id>` - Export profile
- `POST /api/profiles/import` - Import profile

### Actions
- `POST /api/actions/execute` - Execute an action

### Themes
- `GET /api/themes` - Get all themes

### Plugins
- `GET /api/plugins` - Get all plugins
- `GET /api/plugins/<id>/actions` - Get plugin actions

### File Upload
- `POST /api/upload/icon` - Upload custom icon
- `GET /api/uploads/<filename>` - Serve uploaded file

### Configuration
- `GET /api/config` - Get configuration
- `PUT /api/config` - Update configuration

## WebSocket Events

- `connect` - Client connected
- `disconnect` - Client disconnected
- `execute_action` - Execute action (emits `action_result`)

## Action Types

1. **URL Action** - Opens URL in browser
2. **Program Action** - Launches program or file
3. **Command Action** - Executes shell command
4. **Hotkey Action** - Sends keyboard shortcut
5. **Multi Action** - Executes multiple actions
6. **System Control** - Controls volume, media, etc.

## Plugin Development

Create a plugin by extending `BasePlugin`:

```python
from backend.plugins import BasePlugin, PluginInfo

class Plugin(BasePlugin):
    def get_info(self):
        return PluginInfo(
            id='my_plugin',
            name='My Plugin',
            version='1.0.0',
            author='Your Name',
            description='Plugin description',
            actions=['my_action']
        )
    
    def initialize(self):
        # Initialize plugin
        return True
    
    def cleanup(self):
        # Clean up resources
        pass
    
    def execute_action(self, action_id, config):
        # Execute action
        return {'success': True, 'message': 'Action executed'}
    
    def get_action_schema(self, action_id):
        # Return JSON schema for action config
        return {}
```

Place plugin file in `data/plugins/` directory.

