"""
Asset management API routes for VDock
Handles serving and managing assets (icons, animations, backgrounds)
"""

from flask import Blueprint, jsonify, request, send_from_directory, current_app
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import mimetypes

# Create blueprint
assets_bp = Blueprint('assets', __name__, url_prefix='/api/assets')

# Asset directory paths
FRONTEND_ASSETS_DIR = Path(__file__).parent.parent / 'frontend' / 'public' / 'assets'
BACKEND_ASSETS_DIR = Path(__file__).parent.parent / 'Assets'

def get_asset_path(asset_type: str, category: str = None, filename: str = None) -> Path:
    """Get the full path for an asset"""
    base_path = FRONTEND_ASSETS_DIR / asset_type
    
    if category:
        base_path = base_path / category
    
    if filename:
        base_path = base_path / filename
    
    return base_path

def load_json_file(file_path: Path) -> Optional[Dict]:
    """Load and parse a JSON file"""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        current_app.logger.error(f"Error loading JSON file {file_path}: {e}")
    return None

def scan_directory_assets(directory: Path, asset_type: str) -> List[Dict]:
    """Scan a directory for asset files and generate metadata"""
    assets = []
    
    if not directory.exists():
        return assets
    
    # Supported file extensions by type
    extensions = {
        'icons': ['.svg', '.png', '.jpg', '.jpeg', '.webp'],
        'animations': ['.gif', '.webm', '.mp4'],
        'backgrounds': ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.mp4', '.webm']
    }
    
    supported_exts = extensions.get(asset_type, [])
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_exts:
            # Get file info
            stat = file_path.stat()
            relative_path = file_path.relative_to(FRONTEND_ASSETS_DIR)
            
            asset = {
                'id': str(relative_path).replace('\\', '/').replace('/', '_'),
                'name': file_path.stem.replace('_', ' ').replace('-', ' ').title(),
                'category': file_path.parent.name,
                'type': asset_type.rstrip('s'),  # Remove plural
                'format': file_path.suffix.lower().lstrip('.'),
                'size': stat.st_size,
                'url': f'/assets/{relative_path}'.replace('\\', '/'),
                'filename': file_path.name,
                'tags': [file_path.parent.name, file_path.stem.lower()],
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime
            }
            
            # Add dimensions for images
            if asset['format'] in ['png', 'jpg', 'jpeg', 'webp', 'gif']:
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        asset['dimensions'] = {
                            'width': img.width,
                            'height': img.height
                        }
                except ImportError:
                    # PIL not available, skip dimensions
                    pass
                except Exception:
                    # Error reading image, skip dimensions
                    pass
            
            assets.append(asset)
    
    return assets

@assets_bp.route('/metadata')
def get_metadata():
    """Get master asset metadata"""
    metadata_path = FRONTEND_ASSETS_DIR / 'metadata.json'
    metadata = load_json_file(metadata_path)
    
    if metadata:
        return jsonify(metadata)
    else:
        return jsonify({'error': 'Metadata not found'}), 404

@assets_bp.route('/categories')
def get_categories():
    """Get all asset categories"""
    categories = []
    
    # Load icon categories
    icons_index_path = FRONTEND_ASSETS_DIR / 'icons' / 'index.json'
    icons_index = load_json_file(icons_index_path)
    
    if icons_index:
        for category_type, category_map in icons_index.get('categories', {}).items():
            if isinstance(category_map, dict):
                for category_id, index_path in category_map.items():
                    category_data_path = FRONTEND_ASSETS_DIR / index_path
                    category_data = load_json_file(category_data_path)
                    
                    if category_data:
                        categories.append({
                            'id': f"{category_type}_{category_id}",
                            'name': f"{category_type.title()} {category_id.title()}",
                            'type': 'icons',
                            'description': category_data.get('description', ''),
                            'asset_count': len(category_data.get('icons', []))
                        })
    
    # Load background categories
    backgrounds_index_path = FRONTEND_ASSETS_DIR / 'backgrounds' / 'index.json'
    backgrounds_index = load_json_file(backgrounds_index_path)
    
    if backgrounds_index:
        for category_type, index_path in backgrounds_index.get('categories', {}).items():
            if isinstance(index_path, str):
                category_data_path = FRONTEND_ASSETS_DIR / index_path
                category_data = load_json_file(category_data_path)
                
                if category_data:
                    asset_count = 0
                    if 'gradients' in category_data:
                        asset_count = len(category_data['gradients'])
                    elif 'patterns' in category_data:
                        asset_count = len(category_data['patterns'])
                    elif 'images' in category_data:
                        asset_count = len(category_data['images'])
                    
                    categories.append({
                        'id': category_type,
                        'name': category_type.replace('_', ' ').title(),
                        'type': 'backgrounds',
                        'description': category_data.get('description', ''),
                        'asset_count': asset_count
                    })
    
    return jsonify(categories)

@assets_bp.route('/icons')
def get_icons():
    """Get all icon assets"""
    category = request.args.get('category')
    search = request.args.get('search', '').lower()
    
    icons = []
    
    # Load FontAwesome extended icons
    icons_base_path = FRONTEND_ASSETS_DIR / 'icons' / 'fontawesome-extended'
    
    for category_dir in icons_base_path.iterdir():
        if category_dir.is_dir():
            index_path = category_dir / 'index.json'
            category_data = load_json_file(index_path)
            
            if category_data and 'icons' in category_data:
                for icon_data in category_data['icons']:
                    # Apply category filter
                    if category and f"fontawesome_{category_dir.name}" != category:
                        continue
                    
                    # Apply search filter
                    if search and not any(search in field.lower() for field in [
                        icon_data.get('name', ''),
                        icon_data.get('id', ''),
                        ' '.join(icon_data.get('tags', []))
                    ]):
                        continue
                    
                    icon = {
                        'id': icon_data['id'],
                        'name': icon_data['name'],
                        'category': f"fontawesome_{category_dir.name}",
                        'type': 'icon',
                        'format': 'fontawesome',
                        'icon': icon_data['icon'],
                        'color': icon_data.get('color'),
                        'tags': icon_data.get('tags', [])
                    }
                    icons.append(icon)
    
    # Load custom icons from filesystem
    custom_icons_path = FRONTEND_ASSETS_DIR / 'icons' / 'custom'
    if custom_icons_path.exists():
        custom_icons = scan_directory_assets(custom_icons_path, 'icons')
        
        for icon in custom_icons:
            # Apply filters
            if category and not icon['category'].startswith(category):
                continue
            
            if search and not any(search in field.lower() for field in [
                icon['name'], icon['category'], ' '.join(icon['tags'])
            ]):
                continue
            
            icons.append(icon)
    
    return jsonify(icons)

@assets_bp.route('/backgrounds')
def get_backgrounds():
    """Get all background assets"""
    category = request.args.get('category')
    search = request.args.get('search', '').lower()
    
    backgrounds = []
    
    # Load gradient backgrounds
    gradients_path = FRONTEND_ASSETS_DIR / 'backgrounds' / 'dashboard' / 'gradients' / 'index.json'
    gradients_data = load_json_file(gradients_path)
    
    if gradients_data and 'gradients' in gradients_data:
        for gradient_data in gradients_data['gradients']:
            # Apply category filter
            if category and 'dashboard_gradients' != category:
                continue
            
            # Apply search filter
            if search and not any(search in field.lower() for field in [
                gradient_data.get('name', ''),
                gradient_data.get('id', ''),
                ' '.join(gradient_data.get('tags', []))
            ]):
                continue
            
            background = {
                'id': gradient_data['id'],
                'name': gradient_data['name'],
                'category': 'dashboard_gradients',
                'type': 'background',
                'format': 'css',
                'css': gradient_data['css'],
                'colors': gradient_data.get('colors', []),
                'tags': gradient_data.get('tags', [])
            }
            backgrounds.append(background)
    
    # Load file-based backgrounds
    backgrounds_base_path = FRONTEND_ASSETS_DIR / 'backgrounds'
    if backgrounds_base_path.exists():
        file_backgrounds = scan_directory_assets(backgrounds_base_path, 'backgrounds')
        
        for bg in file_backgrounds:
            # Apply filters
            if category and not bg['category'].startswith(category):
                continue
            
            if search and not any(search in field.lower() for field in [
                bg['name'], bg['category'], ' '.join(bg['tags'])
            ]):
                continue
            
            backgrounds.append(bg)
    
    return jsonify(backgrounds)

@assets_bp.route('/animations')
def get_animations():
    """Get all animation assets"""
    category = request.args.get('category')
    search = request.args.get('search', '').lower()
    
    animations = []
    
    # Load file-based animations
    animations_base_path = FRONTEND_ASSETS_DIR / 'animations'
    if animations_base_path.exists():
        file_animations = scan_directory_assets(animations_base_path, 'animations')
        
        for anim in file_animations:
            # Apply filters
            if category and not anim['category'].startswith(category):
                continue
            
            if search and not any(search in field.lower() for field in [
                anim['name'], anim['category'], ' '.join(anim['tags'])
            ]):
                continue
            
            animations.append(anim)
    
    return jsonify(animations)

@assets_bp.route('/search')
def search_assets():
    """Search across all asset types"""
    query = request.args.get('q', '').lower()
    asset_type = request.args.get('type')  # 'icon', 'background', 'animation'
    category = request.args.get('category')
    limit = int(request.args.get('limit', 50))
    
    if not query:
        return jsonify([])
    
    results = []
    
    # Search icons
    if not asset_type or asset_type == 'icon':
        icons_response = get_icons()
        if icons_response.status_code == 200:
            icons = icons_response.get_json()
            results.extend([icon for icon in icons if any(
                query in field.lower() for field in [
                    icon.get('name', ''),
                    icon.get('category', ''),
                    ' '.join(icon.get('tags', []))
                ]
            )])
    
    # Search backgrounds
    if not asset_type or asset_type == 'background':
        backgrounds_response = get_backgrounds()
        if backgrounds_response.status_code == 200:
            backgrounds = backgrounds_response.get_json()
            results.extend([bg for bg in backgrounds if any(
                query in field.lower() for field in [
                    bg.get('name', ''),
                    bg.get('category', ''),
                    ' '.join(bg.get('tags', []))
                ]
            )])
    
    # Search animations
    if not asset_type or asset_type == 'animation':
        animations_response = get_animations()
        if animations_response.status_code == 200:
            animations = animations_response.get_json()
            results.extend([anim for anim in animations if any(
                query in field.lower() for field in [
                    anim.get('name', ''),
                    anim.get('category', ''),
                    ' '.join(anim.get('tags', []))
                ]
            )])
    
    # Apply category filter
    if category:
        results = [asset for asset in results if asset.get('category') == category]
    
    # Limit results
    results = results[:limit]
    
    return jsonify(results)

@assets_bp.route('/file/<path:filename>')
def serve_asset_file(filename):
    """Serve asset files"""
    try:
        # Security check - ensure the path is within assets directory
        asset_path = FRONTEND_ASSETS_DIR / filename
        asset_path = asset_path.resolve()
        
        if not str(asset_path).startswith(str(FRONTEND_ASSETS_DIR.resolve())):
            return jsonify({'error': 'Invalid file path'}), 403
        
        if not asset_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(asset_path))
        
        return send_from_directory(
            str(asset_path.parent),
            asset_path.name,
            mimetype=mime_type
        )
    
    except Exception as e:
        current_app.logger.error(f"Error serving asset file {filename}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assets_bp.route('/upload', methods=['POST'])
def upload_asset():
    """Upload a new asset file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    asset_type = request.form.get('type', 'icons')
    category = request.form.get('category', 'custom')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    allowed_extensions = {
        'icons': ['.svg', '.png', '.jpg', '.jpeg', '.webp'],
        'animations': ['.gif', '.webm', '.mp4'],
        'backgrounds': ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.mp4', '.webm']
    }
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions.get(asset_type, []):
        return jsonify({'error': f'Invalid file type for {asset_type}'}), 400
    
    try:
        # Create upload directory
        upload_dir = get_asset_path(asset_type, category)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / file.filename
        file.save(str(file_path))
        
        # Generate asset metadata
        stat = file_path.stat()
        relative_path = file_path.relative_to(FRONTEND_ASSETS_DIR)
        
        asset = {
            'id': str(relative_path).replace('\\', '/').replace('/', '_'),
            'name': file_path.stem.replace('_', ' ').replace('-', ' ').title(),
            'category': category,
            'type': asset_type.rstrip('s'),
            'format': file_ext.lstrip('.'),
            'size': stat.st_size,
            'url': f'/assets/{relative_path}'.replace('\\', '/'),
            'filename': file.filename,
            'tags': [category, file_path.stem.lower()],
            'uploaded_at': stat.st_ctime
        }
        
        return jsonify({
            'message': 'Asset uploaded successfully',
            'asset': asset
        })
    
    except Exception as e:
        current_app.logger.error(f"Error uploading asset: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@assets_bp.route('/stats')
def get_asset_stats():
    """Get asset repository statistics"""
    stats = {
        'total_assets': 0,
        'by_type': {
            'icons': 0,
            'backgrounds': 0,
            'animations': 0
        },
        'by_category': {},
        'total_size': 0,
        'last_updated': None
    }
    
    try:
        # Count icons
        icons_response = get_icons()
        if icons_response.status_code == 200:
            icons = icons_response.get_json()
            stats['by_type']['icons'] = len(icons)
            stats['total_assets'] += len(icons)
        
        # Count backgrounds
        backgrounds_response = get_backgrounds()
        if backgrounds_response.status_code == 200:
            backgrounds = backgrounds_response.get_json()
            stats['by_type']['backgrounds'] = len(backgrounds)
            stats['total_assets'] += len(backgrounds)
        
        # Count animations
        animations_response = get_animations()
        if animations_response.status_code == 200:
            animations = animations_response.get_json()
            stats['by_type']['animations'] = len(animations)
            stats['total_assets'] += len(animations)
        
        # Calculate total size (for file-based assets)
        if FRONTEND_ASSETS_DIR.exists():
            for file_path in FRONTEND_ASSETS_DIR.rglob('*'):
                if file_path.is_file() and not file_path.name.endswith('.json'):
                    stats['total_size'] += file_path.stat().st_size
        
        return jsonify(stats)
    
    except Exception as e:
        current_app.logger.error(f"Error getting asset stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500
