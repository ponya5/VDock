"""
Weather API routes
"""
from flask import Blueprint, jsonify, request
from actions.weather_action import WeatherAction
import logging


logger = logging.getLogger(__name__)

weather_bp = Blueprint('weather', __name__)


@weather_bp.route('/weather', methods=['GET'])
def get_weather():
    """Get weather data"""
    try:
        # Get parameters from query string - handle both direct and nested params
        location = request.args.get('location') or request.args.get('params[location]', 'auto')
        temp_unit = request.args.get('unit') or request.args.get('params[unit]', 'C')
        refresh_interval = request.args.get('refresh_interval', 15, type=int)
        
        # Debug logging
        logger.info(f"Weather request - Location: {location}, Unit: {temp_unit}, All args: {dict(request.args)}")

        # Execute weather fetch
        config = {
            'weather_location': location,
            'temperature_unit': temp_unit,
            'refresh_interval': refresh_interval
        }

        # Create weather action with config
        weather_action = WeatherAction(config)
        result = weather_action.execute()

        if result.success:
            return jsonify(result.to_dict())
        else:
            return jsonify(result.to_dict()), 400

    except Exception as e:
        logger.error(f"Weather route error: {e}")
        return jsonify({
            'success': False,
            'message': f'Weather service error: {str(e)}',
            'error_code': 1003
        }), 500
