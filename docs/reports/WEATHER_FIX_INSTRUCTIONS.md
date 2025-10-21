# Weather Button Fix - Instructions

## Issue
Weather button shows random values instead of real weather data from WeatherAPI.com

## What Was Changed

### 1. Backend Files Modified
- `backend/app.py` - Added dotenv loading to read environment variables
- `backend/actions/weather_action.py` - Switched to WeatherAPI.com API
- `backend/routes/weather.py` - Added support for nested query parameters
- `backend/config.py` - Added WEATHERAPI_KEY configuration
- `backend/.env` - Added API key: `WEATHERAPI_KEY=862efad301184fd5846194619252110`

### 2. Frontend Files Modified
- `frontend/src/components/WeatherQueryButton.vue` - Updated to display temperature units properly
- `frontend/src/components/ButtonEditor.vue` - Fixed weather action configuration saving

## To Fix The Issue

### Step 1: Restart the Backend
The backend needs to be restarted to load the new environment variables and code changes.

**Windows:**
```bash
# Stop the backend (if running)
# Press Ctrl+C in the backend terminal, or:
taskkill /F /IM python.exe

# Navigate to backend directory
cd backend

# Start the backend
python app.py
```

**Linux/Mac:**
```bash
# Stop the backend
pkill -f "python app.py"

# Navigate to backend directory
cd backend

# Start the backend
python app.py
```

### Step 2: Verify Backend is Working
Open a new terminal and test:

```bash
curl "http://localhost:5000/api/weather?location=London&unit=C"
```

You should see real weather data for London (not "Demo City").

### Step 3: Restart Frontend (if needed)
If the frontend is also running, restart it:

```bash
cd frontend
npm run dev
```

### Step 4: Test in the Browser
1. Open VDock in your browser
2. Edit a weather button
3. Set location to a city name (e.g., "London", "New York", "Tokyo")
4. Choose temperature unit (°C or °F)
5. Save the button
6. The button should now show real weather data for that location

## Verification

The weather button should now:
- ✅ Show real temperature from WeatherAPI.com
- ✅ Display proper temperature units (°C or °F)
- ✅ Update based on the location you set in the button settings
- ✅ Show accurate weather conditions, humidity, wind speed, and visibility

## Troubleshooting

If you still see random values:

1. **Check .env file exists:**
   ```bash
   ls backend/.env
   ```

2. **Verify API key in .env:**
   ```bash
   cat backend/.env | grep WEATHERAPI_KEY
   ```
   Should show: `WEATHERAPI_KEY=862efad301184fd5846194619252110`

3. **Test the API key directly:**
   ```bash
   curl "https://api.weatherapi.com/v1/current.json?key=862efad301184fd5846194619252110&q=London&aqi=no"
   ```
   Should return real London weather data.

4. **Check backend logs:**
   ```bash
   tail -f backend/data/vdock.log
   ```

## Current Status

- ✅ API key configured in backend/.env
- ✅ WeatherAPI.com integration implemented
- ✅ Nested parameter support added
- ✅ Temperature unit display fixed
- ⏳ **Requires backend restart to apply changes**

