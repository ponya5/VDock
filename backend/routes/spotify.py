"""Spotify integration routes."""
from flask import Blueprint, request, jsonify
import uuid

from integrations import SpotifyClient

spotify_bp = Blueprint('spotify', __name__)


@spotify_bp.route('/api/spotify/auth-url', methods=['GET'])
def get_spotify_auth_url():
    """Get Spotify authorization URL."""
    try:
        spotify = SpotifyClient()
        state = str(uuid.uuid4())
        auth_url = spotify.get_auth_url(state)
        return jsonify({
            'auth_url': auth_url,
            'state': state,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/callback', methods=['POST'])
def spotify_callback():
    """Handle Spotify OAuth callback."""
    data = request.json
    code = data.get('code') if data else None
    
    if not code:
        return jsonify({'error': 'No authorization code provided', 'success': False}), 400
    
    try:
        spotify = SpotifyClient()
        token_data = spotify.exchange_code_for_token(code)
        
        return jsonify({
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': token_data['expires_in'],
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/refresh', methods=['POST'])
def spotify_refresh():
    """Refresh Spotify access token."""
    data = request.json
    refresh_token = data.get('refresh_token') if data else None
    
    if not refresh_token:
        return jsonify({'error': 'No refresh token provided', 'success': False}), 400
    
    try:
        spotify = SpotifyClient()
        spotify.refresh_token = refresh_token
        token_data = spotify.refresh_access_token()
        
        return jsonify({
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': token_data['expires_in'],
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/me', methods=['GET'])
def spotify_user():
    """Get Spotify user profile."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header', 'success': False}), 401
    
    try:
        token = auth_header.split(' ')[1]
        spotify = SpotifyClient()
        spotify.set_tokens(token)
        
        user_data = spotify.get_current_user()
        return jsonify({'user': user_data, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/playback', methods=['GET'])
def spotify_playback():
    """Get current Spotify playback state."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header', 'success': False}), 401
    
    try:
        token = auth_header.split(' ')[1]
        spotify = SpotifyClient()
        spotify.set_tokens(token)
        
        playback_data = spotify.get_current_playback()
        return jsonify({'playback': playback_data, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/play', methods=['PUT'])
def spotify_play():
    """Resume Spotify playback."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header', 'success': False}), 401
    
    try:
        token = auth_header.split(' ')[1]
        spotify = SpotifyClient()
        spotify.set_tokens(token)
        
        success = spotify.resume_playback()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/pause', methods=['PUT'])
def spotify_pause():
    """Pause Spotify playback."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header', 'success': False}), 401
    
    try:
        token = auth_header.split(' ')[1]
        spotify = SpotifyClient()
        spotify.set_tokens(token)
        
        success = spotify.pause_playback()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/next', methods=['POST'])
def spotify_next():
    """Skip to next Spotify track."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header', 'success': False}), 401
    
    try:
        token = auth_header.split(' ')[1]
        spotify = SpotifyClient()
        spotify.set_tokens(token)
        
        success = spotify.next_track()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/previous', methods=['POST'])
def spotify_previous():
    """Skip to previous Spotify track."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header', 'success': False}), 401
    
    try:
        token = auth_header.split(' ')[1]
        spotify = SpotifyClient()
        spotify.set_tokens(token)
        
        success = spotify.previous_track()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/volume', methods=['PUT'])
def spotify_volume():
    """Set Spotify volume."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header', 'success': False}), 401
    
    data = request.json
    volume = data.get('volume', 50) if data else 50
    
    try:
        token = auth_header.split(' ')[1]
        spotify = SpotifyClient()
        spotify.set_tokens(token)
        
        success = spotify.set_volume(volume)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/devices', methods=['GET'])
def spotify_devices():
    """Get Spotify devices."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header', 'success': False}), 401
    
    try:
        token = auth_header.split(' ')[1]
        spotify = SpotifyClient()
        spotify.set_tokens(token)
        
        devices = spotify.get_devices()
        return jsonify({'devices': devices, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@spotify_bp.route('/api/spotify/search', methods=['GET'])
def spotify_search():
    """Search Spotify."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header', 'success': False}), 401
    
    query = request.args.get('q', '')
    types = request.args.get('type', 'track').split(',')
    limit = int(request.args.get('limit', 20))
    
    try:
        token = auth_header.split(' ')[1]
        spotify = SpotifyClient()
        spotify.set_tokens(token)
        
        results = spotify.search(query, types, limit)
        return jsonify({'results': results, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
