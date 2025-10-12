# VDock Developer Guide

Guide for developers who want to contribute to VDock or create plugins.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Backend Development](#backend-development)
3. [Frontend Development](#frontend-development)
4. [Plugin Development](#plugin-development)
5. [Building and Packaging](#building-and-packaging)
6. [Testing](#testing)
7. [Contributing](#contributing)

## Project Structure

```
VDock/
├── backend/              # Python Flask backend
│   ├── actions/         # Action executors
│   ├── auth/           # Authentication
│   ├── models/         # Data models
│   ├── plugins/        # Plugin system
│   ├── utils/          # Utilities
│   ├── app.py          # Main Flask app
│   └── config.py       # Configuration
├── frontend/            # Vue 3 frontend
│   ├── src/
│   │   ├── components/ # Vue components
│   │   ├── views/      # Page views
│   │   ├── stores/     # Pinia stores
│   │   ├── api/        # API client
│   │   └── types/      # TypeScript types
│   ├── electron/       # Electron wrapper
│   └── public/         # Static assets
├── docs/               # Documentation
└── README.md
```

## Backend Development

### Setting Up Development Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Adding a New Action Type

1. Create a new file in `backend/actions/`:

```python
from .base_action import BaseAction, ActionResult

class MyAction(BaseAction):
    def validate(self) -> bool:
        # Validate configuration
        return 'my_param' in self.config
    
    def execute(self) -> ActionResult:
        # Execute the action
        param = self.config['my_param']
        try:
            # Do something
            return ActionResult(True, 'Action successful')
        except Exception as e:
            return ActionResult(False, f'Action failed: {str(e)}')
    
    def get_description(self) -> str:
        return f"My action: {self.config.get('my_param')}"
```

2. Register it in `backend/actions/action_executor.py`:

```python
ACTION_CLASSES = {
    # ... existing actions
    'my_action': MyAction
}
```

### Adding API Endpoints

Add routes in `backend/app.py`:

```python
@app.route('/api/my-endpoint', methods=['GET'])
@require_auth
def my_endpoint():
    # Your logic here
    return jsonify({'result': 'data'})
```

### Database/Storage

VDock uses JSON files for storage:

- Profiles: `backend/data/profiles/{id}.json`
- Configuration: `backend/data/config.json`
- Themes: `backend/data/themes/{id}.json`

Use `FileManager` utility for file operations:

```python
from utils import FileManager

# Save
FileManager.save_json(file_path, data)

# Load
data = FileManager.load_json(file_path)
```

## Frontend Development

### Setting Up Development Environment

```bash
cd frontend
npm install
npm run dev
```

### Project Structure

- **components/**: Reusable Vue components
- **views/**: Page-level components (routes)
- **stores/**: Pinia state management
- **api/**: Backend API client
- **types/**: TypeScript type definitions

### Adding a New Component

```vue
<template>
  <div class="my-component">
    <h2>{{ title }}</h2>
    <button @click="handleClick">Click Me</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  title: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  click: []
}>()

function handleClick() {
  emit('click')
}
</script>

<style scoped>
.my-component {
  padding: var(--spacing-md);
}
</style>
```

### Adding a New Store

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useMyStore = defineStore('myStore', () => {
  const data = ref<any[]>([])
  const count = computed(() => data.value.length)

  async function loadData() {
    // Load from API
  }

  return {
    data,
    count,
    loadData
  }
})
```

### Making API Calls

```typescript
import apiClient from '@/api/client'

// GET request
const response = await apiClient.get('/my-endpoint')

// POST request
const response = await apiClient.post('/my-endpoint', { data })

// With authentication (automatic if token is set)
```

### Styling

Use CSS variables for theming:

```css
.my-element {
  background-color: var(--color-surface);
  color: var(--color-text);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
}
```

Available CSS variables:
- Colors: `--color-background`, `--color-surface`, `--color-primary`, etc.
- Spacing: `--spacing-xs` through `--spacing-xl`
- Border radius: `--radius-sm`, `--radius-md`, `--radius-lg`
- Transitions: `--transition-fast`, `--transition-normal`

## Plugin Development

### Plugin Structure

```python
from backend.plugins import BasePlugin, PluginInfo
from typing import Dict, Any

class Plugin(BasePlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            id='my_plugin',
            name='My Plugin',
            version='1.0.0',
            author='Your Name',
            description='What your plugin does',
            actions=['action1', 'action2']
        )
    
    def initialize(self) -> bool:
        # Initialize resources, connections, etc.
        self.my_service = MyService()
        return True
    
    def cleanup(self):
        # Clean up resources
        self.my_service.disconnect()
    
    def execute_action(self, action_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        if action_id == 'action1':
            # Execute action
            return {
                'success': True,
                'message': 'Action executed successfully'
            }
        return {
            'success': False,
            'message': f'Unknown action: {action_id}'
        }
    
    def get_action_schema(self, action_id: str) -> Dict[str, Any]:
        if action_id == 'action1':
            return {
                'type': 'object',
                'properties': {
                    'param1': {
                        'type': 'string',
                        'title': 'Parameter 1',
                        'description': 'Description of parameter'
                    }
                },
                'required': ['param1']
            }
        return {}
```

### Installing Plugins

1. Place plugin file in `backend/data/plugins/`
2. Plugin will be loaded automatically on server start
3. Check logs for loading errors

### Example Plugins

See `backend/plugins/example_obs_plugin.py` for a complete example.

## Building and Packaging

### Frontend Build

```bash
cd frontend
npm run build
```

Builds production-ready files to `frontend/dist/`.

### Electron Build

```bash
cd frontend
npm run build
cd electron
npm install
npm run build
```

Creates Windows installer in `frontend/electron/dist-electron/`.

### Backend Distribution

Backend can be distributed as:

1. **Source**: Distribute Python source code
2. **Executable**: Use PyInstaller to create executable

```bash
pip install pyinstaller
pyinstaller --onefile backend/app.py
```

## Testing

### Backend Tests

```bash
cd backend
pytest
```

Test files in `backend/tests/`.

### Frontend Tests

```bash
cd frontend
npm run test
```

### Manual Testing Checklist

- [ ] Login/authentication
- [ ] Profile creation/loading
- [ ] Button creation/editing
- [ ] All action types work
- [ ] Page navigation
- [ ] Theme switching
- [ ] Profile import/export
- [ ] Settings persistence
- [ ] WebSocket communication
- [ ] Electron features (if desktop app)

## Contributing

### Code Style

**Python (Backend):**
- Follow PEP 8
- Use type hints where appropriate
- Document functions with docstrings

**TypeScript/Vue (Frontend):**
- Use TypeScript for type safety
- Follow Vue 3 Composition API patterns
- Use meaningful component/variable names

### Git Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and commit: `git commit -m "Add my feature"`
4. Push to your fork: `git push origin feature/my-feature`
5. Create a Pull Request

### Commit Messages

Format: `type: description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

Examples:
```
feat: add Spotify plugin
fix: resolve button position bug
docs: update installation instructions
```

### Pull Request Guidelines

- Describe what your PR does
- Link related issues
- Include screenshots for UI changes
- Ensure tests pass
- Update documentation if needed

## Architecture Decisions

### Why Flask?

- Lightweight and flexible
- Excellent WebSocket support via Flask-SocketIO
- Easy to extend with plugins
- Cross-platform Python

### Why Vue 3?

- Reactive and performant
- Excellent TypeScript support
- Composition API for better code organization
- Great ecosystem and tooling

### Why Electron?

- Cross-platform desktop apps
- Access to native APIs
- System tray and global hotkeys
- Familiar web technologies

## Performance Tips

### Backend

- Use async operations where possible
- Cache frequently accessed data
- Minimize file I/O operations
- Profile slow endpoints

### Frontend

- Lazy load components
- Use virtual scrolling for large lists
- Debounce search inputs
- Optimize images

## Security Best Practices

- Validate all user inputs
- Sanitize command executions
- Use HTTPS for remote connections
- Keep dependencies updated
- Follow principle of least privilege

## Debugging

### Backend Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Logs are also written to `backend/data/vdock.log`.

### Frontend Debugging

Use browser DevTools:
- Console for logs
- Network tab for API calls
- Vue DevTools extension for Vue debugging

### Common Issues

**CORS errors:**
- Check CORS_ORIGINS in backend config
- Ensure backend is running

**WebSocket connection fails:**
- Verify backend WebSocket endpoint
- Check firewall settings

**Action execution fails:**
- Check action configuration
- Review backend logs
- Verify required libraries are installed

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Electron Documentation](https://www.electronjs.org/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## Community

- GitHub Discussions: Ask questions and share ideas
- Discord: Join our community server (coming soon)
- Issues: Report bugs and request features

Thank you for contributing to VDock! 🚀

