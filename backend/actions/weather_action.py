"""
Weather Action Handler
Fetches weather data from WeatherAPI.com
"""
import requests
import logging
from typing import Dict, Any
from .base_action import BaseAction, ActionResult
from config import Config

logger = logging.getLogger(__name__)


class WeatherAction(BaseAction):
    """
    Fetch weather data and display it
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Get API key from environment variables
        import os
        self.api_key = os.environ.get('WEATHERAPI_KEY', '')
        self.base_url = "https://api.weatherapi.com/v1/current.json"

    def execute(self) -> ActionResult:
        """
        Execute weather fetch

        Config format:
        {
            "weather_location": "auto" or "city_name",
            "refresh_interval": 15,
            "temperature_unit": "C" or "F"
        }
        """
        try:
            location = self.config.get('weather_location', 'auto')
            temp_unit = self.config.get('temperature_unit', 'C')

            # Check if API key is available
            if not self.api_key:
                logger.warning("WeatherAPI.com API key not configured, using mock data")
                mock_data = self._get_mock_weather_data(location, temp_unit)
                return ActionResult(
                    success=True,
                    message=f"Weather data fetched for {location} (mock data - API key not configured)",
                    data=mock_data['data']
                )

            # Real API implementation using WeatherAPI.com
            params = {
                'key': self.api_key,
                'q': location if location != 'auto' else 'London',
                'aqi': 'no'  # Don't include air quality data
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract weather data from WeatherAPI.com response
            current = data.get('current', {})
            location_info = data.get('location', {})
            
            # Get temperature and convert units if needed
            temp_celsius = current.get('temp_c', 0)
            temp_fahrenheit = current.get('temp_f', 0)
            
            # Get wind speed and visibility
            wind_kph = current.get('wind_kph', 0)
            wind_mph = current.get('wind_mph', 0)
            visibility_km = current.get('vis_km', 0)
            visibility_miles = current.get('vis_miles', 0)
            
            # Format display values based on unit preference
            if temp_unit == 'C':
                temperature = round(temp_celsius)
                wind_speed_display = f"{wind_kph:.1f} km/h"
                visibility_display = f"{visibility_km:.1f} km"
            else:
                temperature = round(temp_fahrenheit)
                wind_speed_display = f"{wind_mph:.1f} mph"
                visibility_display = f"{visibility_miles:.1f} mi"

            return ActionResult(
                success=True,
                message=f"Weather data fetched for {location}",
                data={
                    'location': location_info.get('name', location),
                    'temperature': temperature,
                    'description': current.get('condition', {}).get('text', 'Unknown').title(),
                    'condition': current.get('condition', {}).get('text', 'Unknown').title(),
                    'humidity': current.get('humidity', 0),
                    'windSpeed': wind_speed_display,
                    'visibility': visibility_display,
                    'unit': temp_unit,
                    'unit_symbol': '°C' if temp_unit == 'C' else '°F',
                    'icon': current.get('condition', {}).get('icon', '')
                }
            )

        except requests.RequestException as e:
            logger.error(f"WeatherAPI.com request failed: {e}")
            # Fallback to mock data on API failure
            mock_data = self._get_mock_weather_data(location, temp_unit)
            return ActionResult(
                success=True,
                message=f"Weather data fetched for {location} (fallback data - API unavailable)",
                data=mock_data['data']
            )
        except Exception as e:
            logger.error(f"Weather action error: {e}")
            # Fallback to mock data on any error
            mock_data = self._get_mock_weather_data(location, temp_unit)
            return ActionResult(
                success=True,
                message=f"Weather data fetched for {location} (fallback data - error occurred)",
                data=mock_data['data']
            )

    def _get_mock_weather_data(
        self, location: str, temp_unit: str
    ) -> Dict[str, Any]:
        """Return mock weather data for demo purposes"""
        import random

        if temp_unit == 'C':
            temp = random.randint(-10, 35)
            unit_symbol = '°C'
        else:
            temp = random.randint(14, 95)
            unit_symbol = '°F'

        descriptions = [
            'Clear sky', 'Few clouds', 'Scattered clouds', 'Broken clouds',
            'Shower rain', 'Rain', 'Thunderstorm', 'Snow', 'Mist'
        ]

        description = random.choice(descriptions)
        return {
            'success': True,
            'message': f"Weather data fetched for {location}",
            'data': {
                'location': location if location != 'auto' else 'Demo City',
                'temperature': temp,
                'description': description,
                'condition': description,  # Add condition field
                'humidity': random.randint(30, 90),
                'wind_speed': random.randint(0, 20),
                'unit': temp_unit,
                'unit_symbol': unit_symbol
            }
        }

    def validate(self) -> bool:
        """Validate action configuration"""
        return self.validate_config(self.config)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate weather configuration"""
        required_fields = ['weather_location']

        for field in required_fields:
            if field not in config:
                return False

        location = config.get('weather_location')
        if not location or not isinstance(location, str):
            return False

        temp_unit = config.get('temperature_unit', 'C')
        if temp_unit not in ['C', 'F']:
            return False

        refresh_interval = config.get('refresh_interval', 15)
        if not isinstance(refresh_interval, int) or refresh_interval < 1:
            return False

        return True
