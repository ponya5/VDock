"""Template management routes."""
import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from typing import Dict, Any, List

templates_bp = Blueprint('templates', __name__)

# Templates directory
TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'templates'
)


def get_template_files() -> List[str]:
    """Get all template files in the templates directory."""
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        return []

    return [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.json')]


def load_template(template_id: str) -> Dict[str, Any] | None:
    """Load a template by its ID."""
    template_files = get_template_files()

    for filename in template_files:
        filepath = os.path.join(TEMPLATES_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template = json.load(f)
                if template.get('id') == template_id:
                    return template
        except Exception as e:
            print(f"Error loading template {filename}: {e}")
            continue

    return None


def load_all_templates() -> List[Dict[str, Any]]:
    """Load all available templates."""
    templates = []
    template_files = get_template_files()

    for filename in template_files:
        filepath = os.path.join(TEMPLATES_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template = json.load(f)
                templates.append(template)
        except Exception as e:
            print(f"Error loading template {filename}: {e}")
            continue

    return templates


@templates_bp.route('/list', methods=['GET'])
def list_templates():
    """List all available templates."""
    try:
        templates = load_all_templates()

        # Group templates by category
        categories = {}
        for template in templates:
            category = template.get('category', 'other')
            if category not in categories:
                categories[category] = []

            # Add template summary (without full button data)
            categories[category].append({
                'id': template['id'],
                'name': template['name'],
                'description': template.get('description', ''),
                'icon': template.get('icon', 'fa-star'),
                'color': template.get('color', '#667eea'),
                'category': category,
                'version': template.get('version', '1.0'),
                'author': template.get('author', 'Unknown'),
                'button_count': sum(
                    len(page.get('buttons', []))
                    for page in template.get('pages', [])
                )
            })

        return jsonify({
            'success': True,
            'categories': categories,
            'total_templates': len(templates)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@templates_bp.route('/<template_id>', methods=['GET'])
def get_template(template_id: str):
    """Get a specific template by ID."""
    try:
        template = load_template(template_id)

        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404

        return jsonify({
            'success': True,
            'template': template
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@templates_bp.route('/<template_id>/apply', methods=['POST'])
def apply_template(template_id: str):
    """Apply a template to create a new scene."""
    try:
        template = load_template(template_id)

        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404

        # Generate new IDs for scene, pages, and buttons
        scene = {
            'id': f"scene_{uuid.uuid4().hex[:16]}",
            'name': template['name'],
            'icon': template.get('icon', 'fa-star'),
            'color': template.get('color', '#667eea'),
            'pages': [],
            'isActive': False,
            'buttonSize': 1.0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Create pages with new IDs
        for page_template in template.get('pages', []):
            page = {
                'id': f"page_{uuid.uuid4().hex[:16]}",
                'name': page_template['name'],
                'grid_config': page_template.get(
                    'grid_config', {'rows': 4, 'cols': 5}
                ),
                'buttons': [],
                'background': page_template.get('background')
            }

            # Create buttons with new IDs
            for button_template in page_template.get('buttons', []):
                button = {
                    **button_template,
                    'id': f"btn_{uuid.uuid4().hex[:16]}"
                }
                page['buttons'].append(button)

            scene['pages'].append(page)

        return jsonify({
            'success': True,
            'scene': scene,
            'message': f"Template '{template['name']}' applied successfully"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@templates_bp.route('/export', methods=['POST'])
def export_scene_as_template():
    """Export a scene as a template."""
    try:
        data = request.get_json()

        if not data or 'scene' not in data:
            return jsonify({
                'success': False,
                'error': 'Scene data is required'
            }), 400

        scene = data['scene']
        template_data = data.get('template_data', {})

        # Create template from scene
        template = {
            'id': f"template-{uuid.uuid4().hex[:8]}",
            'name': template_data.get(
                'name', scene.get('name', 'Unnamed Template')
            ),
            'description': template_data.get('description', ''),
            'icon': scene.get('icon', 'fa-star'),
            'color': scene.get('color', '#667eea'),
            'category': template_data.get('category', 'custom'),
            'version': '1.0',
            'author': template_data.get('author', 'User'),
            'pages': scene.get('pages', [])
        }

        # Save template to file
        filename = f"{template['id']}.json"
        filepath = os.path.join(TEMPLATES_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)

        return jsonify({
            'success': True,
            'template_id': template['id'],
            'message': 'Template exported successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@templates_bp.route('/<template_id>', methods=['DELETE'])
def delete_template(template_id: str):
    """Delete a custom template."""
    try:
        # Only allow deletion of custom templates
        protected = (
            not template_id.startswith('template-') or
            template_id.startswith('template-welcome') or
            template_id.startswith('template-ide')
        )
        if protected:
            return jsonify({
                'success': False,
                'error': 'Cannot delete built-in templates'
            }), 403

        template_files = get_template_files()

        for filename in template_files:
            filepath = os.path.join(TEMPLATES_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    if template.get('id') == template_id:
                        os.remove(filepath)
                        return jsonify({
                            'success': True,
                            'message': 'Template deleted successfully'
                        })
            except Exception as e:
                print(f"Error checking template {filename}: {e}")
                continue

        return jsonify({
            'success': False,
            'error': 'Template not found'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@templates_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all template categories."""
    return jsonify({
        'success': True,
        'categories': [
            {
                'id': 'essentials',
                'name': 'Essential Controls',
                'description': 'Basic system and media controls',
                'icon': 'fa-home'
            },
            {
                'id': 'development',
                'name': 'Development',
                'description': 'IDE shortcuts and coding tools',
                'icon': 'fa-code'
            },
            {
                'id': 'gaming',
                'name': 'Gaming',
                'description': 'Game-specific shortcuts and macros',
                'icon': 'fa-gamepad'
            },
            {
                'id': 'streaming',
                'name': 'Streaming',
                'description': 'OBS and streaming controls',
                'icon': 'fa-video'
            },
            {
                'id': 'creative',
                'name': 'Creative',
                'description': 'Adobe, music production, and design tools',
                'icon': 'fa-palette'
            },
            {
                'id': 'productivity',
                'name': 'Productivity',
                'description': 'Workflow automation and productivity tools',
                'icon': 'fa-briefcase'
            },
            {
                'id': 'custom',
                'name': 'Custom',
                'description': 'User-created templates',
                'icon': 'fa-user'
            }
        ]
    })
