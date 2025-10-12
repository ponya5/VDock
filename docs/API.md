# VDock API Documentation

Complete API reference for VDock backend.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST /api/auth/login

Authenticate and receive a JWT token.

**Request:**
```json
{
  "password": "your-password"
}
```

**Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "success": true
}
```

#### GET /api/auth/verify

Verify if the current token is valid.

**Headers:** Requires authentication

**Response:**
```json
{
  "valid": true
}
```

### Profiles

#### GET /api/profiles

Get all profiles (summary only).

**Headers:** Requires authentication

**Response:**
```json
{
  "profiles": [
    {
      "id": "uuid",
      "name": "Profile Name",
      "description": "Description",
      "icon": "fas fa-folder",
      "theme": "dark",
      "page_count": 3
    }
  ]
}
```

#### GET /api/profiles/<profile_id>

Get a specific profile with all details.

**Headers:** Requires authentication

**Response:**
```json
{
  "profile": {
    "id": "uuid",
    "name": "Profile Name",
    "description": "Description",
    "icon": "fas fa-folder",
    "pages": [...],
    "theme": "dark",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### POST /api/profiles

Create a new profile.

**Headers:** Requires authentication

**Request:**
```json
{
  "name": "Profile Name",
  "description": "Optional description",
  "theme": "dark"
}
```

**Response:**
```json
{
  "profile": {...},
  "success": true
}
```

#### PUT /api/profiles/<profile_id>

Update an existing profile.

**Headers:** Requires authentication

**Request:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "theme": "light",
  "pages": [...]
}
```

**Response:**
```json
{
  "profile": {...},
  "success": true
}
```

#### DELETE /api/profiles/<profile_id>

Delete a profile.

**Headers:** Requires authentication

**Response:**
```json
{
  "success": true
}
```

#### POST /api/profiles/<profile_id>/duplicate

Duplicate an existing profile.

**Headers:** Requires authentication

**Response:**
```json
{
  "profile": {...},
  "success": true
}
```

#### GET /api/profiles/export/<profile_id>

Export a profile as JSON.

**Headers:** Requires authentication

**Response:**
```json
{
  "profile": {...},
  "success": true
}
```

#### POST /api/profiles/import

Import a profile from JSON.

**Headers:** Requires authentication

**Request:**
```json
{
  "profile": {...}
}
```

**Response:**
```json
{
  "profile": {...},
  "success": true
}
```

### Actions

#### POST /api/actions/execute

Execute an action.

**Headers:** Requires authentication

**Request:**
```json
{
  "action": {
    "type": "url",
    "config": {
      "url": "https://google.com"
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Opened URL: https://google.com",
  "data": {}
}
```

### Themes

#### GET /api/themes

Get all available themes.

**Headers:** Requires authentication

**Response:**
```json
{
  "themes": [
    {
      "id": "dark",
      "name": "Dark",
      "colors": {
        "background": "#1a1a1a",
        "surface": "#2d2d2d",
        ...
      }
    }
  ]
}
```

### Plugins

#### GET /api/plugins

Get all loaded plugins.

**Headers:** Requires authentication

**Response:**
```json
{
  "plugins": [
    {
      "id": "obs_studio",
      "name": "OBS Studio",
      "version": "1.0.0",
      "author": "VDock",
      "description": "Control OBS Studio",
      "actions": ["obs_start_recording", ...]
    }
  ]
}
```

#### GET /api/plugins/<plugin_id>/actions

Get actions provided by a plugin.

**Headers:** Requires authentication

**Response:**
```json
{
  "actions": [
    {
      "id": "obs_start_recording",
      "schema": {...}
    }
  ]
}
```

### File Upload

#### POST /api/upload/icon

Upload a custom icon.

**Headers:** Requires authentication

**Request:** multipart/form-data with file

**Response:**
```json
{
  "filename": "uuid.png",
  "url": "/api/uploads/uuid.png",
  "success": true
}
```

#### GET /api/uploads/<filename>

Serve an uploaded file.

**Response:** File content

### Configuration

#### GET /api/config

Get server configuration.

**Headers:** Requires authentication

**Response:**
```json
{
  "config": {
    "host": "127.0.0.1",
    "port": 5000,
    "require_auth": true,
    "allow_lan": false,
    "use_ssl": false
  }
}
```

#### PUT /api/config

Update server configuration.

**Headers:** Requires authentication

**Request:**
```json
{
  "allow_lan": true,
  "use_ssl": false
}
```

**Response:**
```json
{
  "success": true
}
```

### Health Check

#### GET /api/health

Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "plugins_loaded": 2
}
```

## WebSocket Events

Connect to: `ws://localhost:5000`

### Client -> Server

#### execute_action

Execute an action via WebSocket.

**Payload:**
```json
{
  "action": {
    "type": "url",
    "config": {
      "url": "https://google.com"
    }
  }
}
```

### Server -> Client

#### connected

Sent when client connects.

**Payload:**
```json
{
  "message": "Connected to VDock server"
}
```

#### action_result

Result of an action execution.

**Payload:**
```json
{
  "success": true,
  "message": "Opened URL: https://google.com",
  "data": {}
}
```

## Action Types

### URL Action

```json
{
  "type": "url",
  "config": {
    "url": "https://example.com"
  }
}
```

### Program Action

```json
{
  "type": "program",
  "config": {
    "path": "C:\\Program Files\\App\\app.exe",
    "args": ["--flag"],
    "working_dir": "C:\\path"
  }
}
```

### Command Action

```json
{
  "type": "command",
  "config": {
    "command": "echo Hello",
    "require_confirmation": true,
    "confirmed": false
  }
}
```

### Hotkey Action

```json
{
  "type": "hotkey",
  "config": {
    "keys": ["ctrl", "c"],
    "delay": 0.05
  }
}
```

### Multi-Action

```json
{
  "type": "multi_action",
  "config": {
    "actions": [
      {"type": "url", "config": {"url": "https://example.com"}},
      {"type": "program", "config": {"path": "notepad.exe"}}
    ],
    "delay": 0.1,
    "stop_on_error": false
  }
}
```

### System Control

```json
{
  "type": "system_control",
  "config": {
    "action": "volume_up"
  }
}
```

Valid actions:
- `volume_up`
- `volume_down`
- `volume_mute`
- `volume_set` (requires `level` parameter 0-100)
- `media_play_pause`
- `media_next`
- `media_previous`
- `media_stop`

## Error Responses

All endpoints may return error responses:

```json
{
  "error": "Error message",
  "success": false
}
```

Common HTTP status codes:
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

Currently no rate limiting is implemented, but it's recommended to:
- Limit action execution to reasonable frequencies
- Avoid rapid profile updates
- Cache data where possible

