# New Action Types Guide

## 🎉 Three Powerful New Button Types Added!

VDock now supports three advanced button action types that transform your dashboard into a comprehensive control center with real-time information and utilities.

---

## 1. 📊 System Performance Monitor

**Display multiple system metrics in a single button**

### Features
- **Multi-metric Display**: Show up to 12 different system metrics simultaneously
- **Real-time Updates**: Auto-refresh at configurable intervals (1-60 seconds)
- **Visual Indicators**: Progress bars, color-coded status, icons
- **Comprehensive Metrics**: CPU, Memory, Disk, GPU, Network, and more

### Available Metrics
1. **Memory** - RAM usage percentage
2. **CPU Usage** - Processor utilization
3. **CPU Temperature** - Processor temperature in °C
4. **CPU Frequency** - Current clock speed in MHz
5. **CPU Package Power** - Power consumption in Watts
6. **Internet Speed** - Network download speed in Mbps
7. **Harddisk** - Disk space usage percentage
8. **GPU Temperature** - Graphics card temperature in °C
9. **GPU Core Frequency** - GPU clock speed in MHz
10. **GPU Core Usage** - Graphics processor utilization
11. **GPU Memory Frequency** - VRAM clock speed in MHz
12. **GPU Memory Usage** - Video memory utilization

### How to Create
1. Add new button → Action Type: **System Performance Monitor**
2. Check the metrics you want to monitor
3. Set refresh interval (default: 2 seconds)
4. Save!

### Best Use Cases
- **Gaming Rig Dashboard**: Monitor CPU temp, GPU usage, FPS metrics
- **Workstation Monitor**: Track system resources during rendering/compilation
- **Server Monitoring**: Keep an eye on critical system metrics
- **Development**: Monitor resource usage while testing

---

## 2. 🕐 Time Options

**World clocks, timers, and countdowns at your fingertips**

### Three Modes

#### A. World Time
Display time from any timezone around the world.

**Features**:
- Live clock with seconds
- Date display
- 11 major timezones + local time
- Automatic timezone conversion

**Available Timezones**:
- Local Time
- New York (EST/EDT)
- Chicago (CST/CDT)
- Denver (MST/MDT)
- Los Angeles (PST/PDT)
- London (GMT/BST)
- Paris (CET/CEST)
- Tokyo (JST)
- Shanghai (CST)
- Dubai (GST)
- Sydney (AEST/AEDT)

#### B. Timer (Stopwatch)
Interactive timer with play/pause and reset controls.

**Features**:
- Start/Stop timer
- Reset function
- Hours:Minutes:Seconds format
- Perfect for tracking work sessions, exercises, cooking

#### C. Countdown
Count down to a specific date and time.

**Features**:
- Set target date/time
- Auto-calculates time remaining
- Progress bar showing elapsed time
- Perfect for deadlines, events, launches

### How to Create
1. Add new button → Action Type: **Time Options**
2. Select mode: World Time, Timer, or Countdown
3. Configure based on mode:
   - **World Time**: Choose timezone
   - **Timer**: Set initial duration (0 for stopwatch)
   - **Countdown**: Set target date/time
4. Save!

### Best Use Cases
- **Remote Teams**: Display teammate timezones
- **Productivity**: Pomodoro timer (25 min work sessions)
- **Events**: Countdown to product launches, deadlines
- **Cooking**: Kitchen timers for recipes
- **Time Tracking**: Bill able hours, project time

---

## 3. 🌤️ Weather Query

**Live weather information right on your dashboard**

### Features
- **Current Weather**: Temperature, conditions, description
- **Detailed Metrics**: Humidity, wind speed, visibility
- **Beautiful UI**: Dynamic gradient backgrounds based on weather
- **Auto-location**: Automatically detect your location
- **Custom Locations**: Enter any city name
- **Smart Icons**: Weather-specific icons (sun, clouds, rain, snow, etc.)
- **Auto-refresh**: Updates every 15 minutes (configurable 5-120 min)

### Weather Conditions
The button automatically changes appearance based on current weather:
- ☀️ **Clear/Sunny**: Warm gradient (pink/orange)
- ☁️ **Cloudy**: Light blue gradient
- 🌧️ **Rainy**: Deep purple gradient
- ❄️ **Snowy**: Light purple/blue gradient
- ⛈️ **Stormy**: Dark gray/black gradient

### Displayed Information
- **Large Temperature Display**: Current temp in °F or °C
- **Weather Description**: "Partly Cloudy", "Clear Sky", etc.
- **Location**: City/region name
- **Humidity**: Percentage
- **Wind Speed**: mph or km/h
- **Visibility**: Distance in miles/km

### How to Create
1. Add new button → Action Type: **Weather Query**
2. Enter location:
   - Type "auto" for automatic detection
   - Or enter city name (e.g., "New York", "London", "Tokyo")
3. Set refresh interval (default: 15 minutes)
4. Save!

### Best Use Cases
- **Home Dashboard**: Morning weather check
- **Travel Planning**: Monitor destination weather
- **Outdoor Activities**: Quick weather glance for hiking, sports
- **Photography**: Track lighting conditions
- **Smart Home**: Integrate with AC/heating decisions

---

## 📋 Setup Instructions

### Quick Start

**Performance Monitor**:
```
1. Dashboard → Edit Mode → Add Button
2. Action Type: System Performance Monitor
3. Select: Memory, CPU Usage, GPU Temperature
4. Refresh: 2 seconds
5. Label: "System Monitor"
6. Save
```

**World Time**:
```
1. Dashboard → Edit Mode → Add Button
2. Action Type: Time Options
3. Type: World Time
4. Timezone: Tokyo (JST)
5. Label: "Tokyo Time"
6. Save
```

**Weather**:
```
1. Dashboard → Edit Mode → Add Button
2. Action Type: Weather Query
3. Location: auto
4. Refresh: 15 minutes
5. Label: "Weather"
6. Save
```

---

## 🎨 Customization Tips

### Performance Monitor
- **Choose relevant metrics**: Don't overload with too many
- **Larger buttons**: Use 2x2 or 2x3 for better readability
- **Grouped dashboards**: Create pages for different monitoring needs

### Time Options
- **Team dashboard**: Create buttons for each team member's timezone
- **Productivity page**: Multiple timers for different tasks
- **Event tracking**: Countdowns for important deadlines

### Weather
- **Multiple locations**: Track weather in different cities
- **Travel dashboard**: Weather for home + destination
- **Outdoor page**: Weather + relevant timers/schedules

---

## 💡 Pro Tips

1. **Button Size**: These action types work best with larger buttons (2x2 or bigger)
2. **Refresh Rates**: Balance between freshness and performance
   - Performance Monitor: 2-5 seconds
   - Weather: 15-30 minutes
3. **Combinations**: Create themed dashboards
   - "Morning Dashboard": Weather + World Times + Timer
   - "Work Monitor": Performance + Timer + Countdown to deadline
4. **Visual Effects**: Apply glass-morphism or gradient effects for modern look
5. **Positioning**: Place information buttons in corners, action buttons in center

---

## 🔧 Technical Details

### Performance Monitor
- **Backend**: Uses existing `/metrics/*` endpoints
- **Update Method**: Polling at configured interval
- **Data Source**: `psutil`, `GPUtil` libraries
- **Supported Platforms**: Windows, macOS, Linux

### Time Options
- **World Time**: Uses browser's `Intl` API for timezone conversion
- **Timer**: Client-side JavaScript interval
- **Countdown**: Calculates difference to target datetime
- **No Backend**: Runs entirely in browser

### Weather Query
- **Backend Endpoint**: `/weather` (to be implemented)
- **Fallback**: Mock data for demo purposes
- **Update Method**: Periodic API calls
- **Location**: IP-based or manual entry

---

## 🐛 Troubleshooting

### Performance Monitor Not Updating
- Check refresh interval is set (min 1 second)
- Verify backend metrics endpoints are accessible
- Ensure required libraries installed (`psutil`, `GPUtil`)

### Time Options Clock Skew
- Check system time is correct
- Verify timezone selection
- Ensure browser has correct locale

### Weather Not Loading
- Verify location is valid city name
- Check network connectivity
- Backend weather API may need setup

---

## 📚 Related Documentation

- [Complete Features Guide](./COMPLETE_FEATURES_GUIDE.md)
- [System Metrics Documentation](./NEW_FEATURES_SUMMARY.md)
- [Button Customization Guide](./USER_GUIDE.md)

---

**Transform your dashboard into an information hub with these powerful new button types! 🚀**

