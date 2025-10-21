"""
Weather Action Handler
Fetches weather data from OpenWeatherMap API
"""
import requests
import logging
from typing import Dict, Any
from .base_action import BaseAction, ActionResult

logger = logging.getLogger(__name__)


class WeatherAction(BaseAction):
    """
    Fetch weather data and display it
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # You can set your OpenWeatherMap API key here or in environment
        # variables
        self.api_key = "demo_key"  # Replace with actual API key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

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

            # For demo purposes, return mock weather data
            # In production, you would fetch from OpenWeatherMap API
            if self.api_key == "demo_key":
                mock_data = self._get_mock_weather_data(location, temp_unit)
                return ActionResult(
                    success=True,
                    message=f"Weather data fetched for {location}",
                    data=mock_data['data']
                )

            # Real API implementation would go here
            params = {
                'q': location if location != 'auto' else 'London',
                'appid': self.api_key,
                'units': 'metric' if temp_unit == 'C' else 'imperial'
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            return ActionResult(
                success=True,
                message=f"Weather data fetched for {location}",
                data={
                    'location': data.get('name', location),
                    'temperature': data['main']['temp'],
                    'description': data['weather'][0]['description'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': data['wind']['speed'],
                    'unit': temp_unit
                }
            )

        except requests.RequestException as e:
            logger.error(f"Weather API request failed: {e}")
            return ActionResult(
                success=False,
                message=f'Failed to fetch weather data: {str(e)}',
                error_code=1001
            )
        except Exception as e:
            logger.error(f"Weather action error: {e}")
            return ActionResult(
                success=False,
                message=f'Weather action failed: {str(e)}',
                error_code=1002
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

        return {
            'success': True,
            'message': f"Weather data fetched for {location}",
            'data': {
                'location': location if location != 'auto' else 'Demo City',
                'temperature': temp,
                'description': random.choice(descriptions),
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
