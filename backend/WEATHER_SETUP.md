# Weather API Setup Instructions

## Overview
The weather button uses real weather data from WeatherAPI.com. A demo API key is included for immediate functionality, but for production use you should get your own free API key.

## Quick Start (Demo Mode)
The app includes a demo API key that works immediately but has limited usage. Weather buttons will show real data for basic testing.

## Production Setup (Recommended)

1. **Get a Free API Key**
   - Visit [WeatherAPI.com](https://www.weatherapi.com/)
   - Sign up for a free account (1 million calls/month free)
   - Go to your dashboard to get your API key
   - Copy your API key

2. **Configure Your API Key**
   - Copy `env.example` to `.env` in the backend directory
   - Replace the demo key with your API key:
     ```
     WEATHERAPI_KEY=your-actual-api-key-here
     ```

3. **Restart the Backend**
   - Restart the VDock backend to load the new environment variables

## Features

- **Real Weather Data**: Uses WeatherAPI.com for accurate weather information
- **Location Support**: Supports both "auto" location and specific city names
- **Unit Selection**: Choose between Celsius (°C) and Fahrenheit (°F)
- **Smart Fallback**: Automatically falls back to demo data if API fails or limits exceeded
- **Proper Units**: Wind speed and visibility are displayed in appropriate units based on temperature unit selection
- **Demo Mode**: Works immediately with included demo API key

## Configuration Options

In the weather button settings:
- **Location**: Enter city name or "auto" for automatic location detection
- **Temperature Unit**: Choose Celsius (°C) or Fahrenheit (°F)
- **Refresh Interval**: How often to update weather data (5-120 minutes)

## Troubleshooting

- **Demo Mode**: If you see "demo mode" messages, the app is using the included demo API key
- **Rate Limits**: If you exceed the demo key limits, weather will fall back to demo data
- **Invalid Key**: If you get "API key invalid" messages, check your `.env` file configuration
- **Location Issues**: Try common city names like "London", "New York", "Tokyo"
- **Backend Logs**: Check backend logs for detailed error information

## Demo Key Limitations

The included demo API key has these limitations:
- Limited daily requests (shared among all users)
- May hit rate limits during peak usage
- For production use, get your own free API key at weatherapi.com
