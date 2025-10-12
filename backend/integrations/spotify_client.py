"""Spotify Web API client for VDock integration."""
import requests
import base64
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from config import Config


class SpotifyClient:
    """Spotify Web API client."""
    
    BASE_URL = 'https://api.spotify.com/v1'
    AUTH_URL = 'https://accounts.spotify.com/api/token'
    
    def __init__(self):
        """Initialize Spotify client."""
        self.client_id = Config.SPOTIFY_CLIENT_ID
        self.client_secret = Config.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = Config.SPOTIFY_REDIRECT_URI
        self.scope = Config.SPOTIFY_SCOPE
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
    
    def get_auth_url(self, state: str = None) -> str:
        """Generate Spotify authorization URL."""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': self.scope
        }
        if state:
            params['state'] = state
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f'https://accounts.spotify.com/authorize?{query_string}'
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        auth_string = f'{self.client_id}:{self.client_secret}'
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(self.AUTH_URL, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        self.refresh_token = token_data.get('refresh_token')
        self.token_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
        
        return token_data
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            raise ValueError('No refresh token available')
        
        auth_string = f'{self.client_id}:{self.client_secret}'
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        response = requests.post(self.AUTH_URL, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        if 'refresh_token' in token_data:
            self.refresh_token = token_data['refresh_token']
        self.token_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
        
        return token_data
    
    def _ensure_valid_token(self):
        """Ensure access token is valid, refresh if needed."""
        if not self.access_token:
            raise ValueError('No access token available')
        
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            self.refresh_access_token()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Spotify API."""
        self._ensure_valid_token()
        
        url = f'{self.BASE_URL}{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        
        kwargs['headers'] = headers
        
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        
        return response.json() if response.content else {}
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current user profile."""
        return self._make_request('GET', '/me')
    
    def get_current_playback(self) -> Dict[str, Any]:
        """Get current playback state."""
        return self._make_request('GET', '/me/player')
    
    def get_currently_playing(self) -> Dict[str, Any]:
        """Get currently playing track."""
        return self._make_request('GET', '/me/player/currently-playing')
    
    def pause_playback(self) -> bool:
        """Pause current playback."""
        try:
            self._make_request('PUT', '/me/player/pause')
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def resume_playback(self) -> bool:
        """Resume current playback."""
        try:
            self._make_request('PUT', '/me/player/play')
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def toggle_playback(self) -> bool:
        """Toggle playback (play/pause)."""
        try:
            playback = self.get_current_playback()
            if playback.get('is_playing'):
                return self.pause_playback()
            else:
                return self.resume_playback()
        except requests.exceptions.HTTPError:
            return False
    
    def next_track(self) -> bool:
        """Skip to next track."""
        try:
            self._make_request('POST', '/me/player/next')
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def previous_track(self) -> bool:
        """Skip to previous track."""
        try:
            self._make_request('POST', '/me/player/previous')
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def set_volume(self, volume_percent: int) -> bool:
        """Set playback volume (0-100)."""
        try:
            self._make_request('PUT', f'/me/player/volume?volume_percent={volume_percent}')
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def seek_to_position(self, position_ms: int) -> bool:
        """Seek to position in current track."""
        try:
            self._make_request('PUT', f'/me/player/seek?position_ms={position_ms}')
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get available devices."""
        response = self._make_request('GET', '/me/player/devices')
        return response.get('devices', [])
    
    def transfer_playback(self, device_id: str) -> bool:
        """Transfer playback to specific device."""
        try:
            data = {'device_ids': [device_id]}
            self._make_request('PUT', '/me/player', json=data)
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def search(self, query: str, types: List[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Search for tracks, artists, albums, etc."""
        if types is None:
            types = ['track']
        
        params = {
            'q': query,
            'type': ','.join(types),
            'limit': limit
        }
        
        return self._make_request('GET', '/search', params=params)
    
    def get_track(self, track_id: str) -> Dict[str, Any]:
        """Get track details."""
        return self._make_request('GET', f'/tracks/{track_id}')
    
    def get_album(self, album_id: str) -> Dict[str, Any]:
        """Get album details."""
        return self._make_request('GET', f'/albums/{album_id}')
    
    def get_artist(self, artist_id: str) -> Dict[str, Any]:
        """Get artist details."""
        return self._make_request('GET', f'/artists/{artist_id}')
    
    def get_user_playlists(self, limit: int = 20) -> Dict[str, Any]:
        """Get user's playlists."""
        return self._make_request('GET', f'/me/playlists?limit={limit}')
    
    def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist details."""
        return self._make_request('GET', f'/playlists/{playlist_id}')
    
    def play_track(self, track_id: str, device_id: str = None) -> bool:
        """Play specific track."""
        try:
            data = {'uris': [f'spotify:track:{track_id}']}
            if device_id:
                data['device_id'] = device_id
            
            self._make_request('PUT', '/me/player/play', json=data)
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def play_playlist(self, playlist_id: str, device_id: str = None) -> bool:
        """Play specific playlist."""
        try:
            data = {'context_uri': f'spotify:playlist:{playlist_id}'}
            if device_id:
                data['device_id'] = device_id
            
            self._make_request('PUT', '/me/player/play', json=data)
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def set_tokens(self, access_token: str, refresh_token: str = None, expires_in: int = None):
        """Set tokens manually."""
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        if expires_in:
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    def get_token_info(self) -> Dict[str, Any]:
        """Get current token information."""
        return {
            'has_access_token': bool(self.access_token),
            'has_refresh_token': bool(self.refresh_token),
            'expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'is_expired': self.token_expires_at and datetime.now() >= self.token_expires_at if self.token_expires_at else False
        }
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return bool(self.access_token)
