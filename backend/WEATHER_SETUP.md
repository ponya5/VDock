# Weather API Setup Instructions

## Overview
The weather button now uses real weather data from WeatherAPI.com instead of random mock data. To enable real weather data, you need to configure an API key.

## Setup Steps

1. **Get a Free API Key**
   - Visit [WeatherAPI.com](https://www.weatherapi.com/)
   - Sign up for a free account
   - Go to your dashboard to get your API key
   - Copy your API key

2. **Configure the API Key**
   - Copy `env.example` to `.env` in the backend directory
   - Add your API key to the `.env` file:
     ```
     WEATHERAPI_KEY=your-actual-api-key-here
     ```

3. **Restart the Backend**
   - Restart the VDock backend to load the new environment variables

## Features

- **Real Weather Data**: Uses WeatherAPI.com for accurate weather information
- **Location Support**: Supports both "auto" location and specific city names
- **Unit Selection**: Choose between Celsius (°C) and Fahrenheit (°F)
- **Fallback**: If API key is not configured or API fails, falls back to mock data
- **Proper Units**: Wind speed and visibility are displayed in appropriate units based on temperature unit selection

## Configuration Options

In the weather button settings:
- **Location**: Enter city name or "auto" for automatic location detection
- **Temperature Unit**: Choose Celsius (°C) or Fahrenheit (°F)
- **Refresh Interval**: How often to update weather data (5-120 minutes)

## Troubleshooting

- If weather shows mock data, check that your API key is correctly configured
- If API calls fail, the system will automatically fall back to mock data
- Check backend logs for any API-related errors
- Verify the location name is valid (try common city names like "London", "New York", "Tokyo")
