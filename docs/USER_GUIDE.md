# VDock User Guide

Complete guide to using VDock Virtual Stream Deck.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Your First Profile](#creating-your-first-profile)
3. [Working with Buttons](#working-with-buttons)
4. [Action Types](#action-types)
5. [Customization](#customization)
6. [Profiles and Organization](#profiles-and-organization)
7. [Tips and Tricks](#tips-and-tricks)

## Getting Started

### Installation

Follow the installation instructions in the main README.md to set up VDock on your system.

### First Launch

1. Start the backend server
2. Open the frontend or launch the desktop app
3. Login with your password (default: `admin`)
4. You'll see the main deck view

### Interface Overview

The VDock interface consists of:

- **Header**: Profile name, navigation, and action buttons
- **Main Deck Area**: Grid of interactive buttons
- **Page Navigation**: Switch between pages (if multiple pages exist)
- **Edit Mode Toolbar**: Appears when editing (bottom of screen)

## Creating Your First Profile

### What is a Profile?

A profile is a collection of pages and buttons organized for a specific purpose. For example:
- **Streaming Profile**: OBS controls, chat commands, scene switching
- **Work Profile**: Frequently used apps, file shortcuts, productivity tools
- **Gaming Profile**: Game launchers, voice chat controls, macros

### Creating a Profile

1. Click the folder icon in the header or navigate to Profiles
2. Click "New Profile"
3. Enter a name and description
4. Click "Create"

Your new profile will be created with one empty page.

## Working with Buttons

### Adding a Button

1. Enter Edit Mode by clicking the edit icon in the header
2. Click "Add Button" in the toolbar
3. Configure the button properties
4. Click "Save"

### Button Properties

#### Basic Properties

- **Label**: Main text displayed on the button
- **Secondary Label**: Smaller text below the main label
- **Icon**: Visual icon (Font Awesome or custom image)
- **Shape**: Rectangle, Rounded, or Circle
- **Tooltip**: Hover text description

#### Position and Size

- **Position**: Row and column in the grid
- **Size**: How many rows/columns the button spans

#### Action

The action determines what happens when you click the button. See [Action Types](#action-types) below.

### Editing a Button

1. Enter Edit Mode
2. Click the button you want to edit
3. Make your changes
4. Click "Save"

### Deleting a Button

1. Enter Edit Mode
2. Hover over the button
3. Click the trash icon
4. Confirm deletion

### Moving Buttons

1. Enter Edit Mode
2. Edit the button
3. Change the Position (row/column)
4. Save

## Action Types

### Open URL

Opens a website or web app in your default browser.

**Configuration:**
- **URL**: The web address (e.g., `https://google.com`)

**Examples:**
- Open Gmail: `https://gmail.com`
- Open YouTube: `https://youtube.com`
- Open local file: `file:///C:/path/to/file.html`

### Launch Program

Starts an application or opens a file.

**Configuration:**
- **Path**: Full path to the executable or file

**Examples:**
- Open Notepad: `C:\Windows\System32\notepad.exe`
- Open Calculator: `calc.exe`
- Open a document: `C:\Users\YourName\Documents\file.docx`

**Tips:**
- Use Windows search to find the executable location
- For apps in PATH, just use the program name

### Run Command

Executes a shell command or script.

**Configuration:**
- **Command**: The command to execute

**Examples:**
- Shutdown computer: `shutdown /s /t 0`
- Open Command Prompt: `cmd`
- Run a script: `python C:\scripts\my_script.py`

**Warning:** Be careful with commands. They execute with your user permissions.

### Send Hotkey

Simulates keyboard shortcuts.

**Configuration:**
- **Keys**: Comma-separated list of keys (e.g., `ctrl, c`)

**Examples:**
- Copy: `ctrl, c`
- Paste: `ctrl, v`
- Save: `ctrl, s`
- Alt+Tab: `alt, tab`
- Media Play/Pause: `media_play_pause`

**Supported Keys:**
- Modifiers: `ctrl`, `alt`, `shift`, `win`
- Letters: `a`-`z`
- Numbers: `0`-`9`
- Function keys: `f1`-`f12`
- Special: `enter`, `tab`, `space`, `backspace`, `delete`, `escape`
- Arrows: `up`, `down`, `left`, `right`
- Media: `media_play_pause`, `media_next`, `media_previous`

### Multi-Action

Executes multiple actions in sequence.

**Configuration:**
- **Actions**: List of actions to execute
- **Delay**: Time between actions (milliseconds)
- **Stop on Error**: Whether to stop if an action fails

**Examples:**
- Open multiple websites
- Launch several programs at once
- Execute a sequence of commands

### System Control

Controls system functions.

**Options:**
- Volume Up
- Volume Down
- Mute/Unmute
- Play/Pause Media
- Next Track
- Previous Track

**Note:** System controls work natively on Windows. Other platforms may require additional setup.

## Customization

### Themes

Change the overall appearance:

1. Go to Settings
2. Select a theme:
   - **Dark**: Default dark theme
   - **Light**: Light theme for bright environments
   - **High Contrast**: Accessibility-friendly high contrast

### Button Appearance

Customize individual buttons:

1. Edit the button
2. Scroll to styling options
3. Adjust:
   - Background color
   - Text color
   - Border color
   - Border width
   - Icon size
   - Font size

### Page Background

Set a background for the entire page:

1. This feature is coming in a future update
2. Currently pages use the theme background

### Icons

#### Using Font Awesome Icons

Format: `fas fa-icon-name` or `fab fa-brand-name`

Examples:
- Home: `fas fa-home`
- User: `fas fa-user`
- Twitter: `fab fa-twitter`
- Discord: `fab fa-discord`

Use the Icon Picker to browse available icons.

#### Custom Icons

1. In button editor, click "Upload Custom Icon"
2. Select an image file (PNG, JPG, SVG)
3. Icon will be uploaded and applied

## Profiles and Organization

### Multiple Pages

Organize buttons across multiple pages:

1. Pages are created automatically as needed
2. Use page navigation to switch between pages
3. Swipe left/right on touch devices
4. Use folder buttons to link to other pages

### Profile Switching

Quickly switch between profiles:

1. Go to Profiles page
2. Click "Load" on the desired profile
3. Or use the profile switcher (coming soon)

### Importing and Exporting

#### Export a Profile

1. Go to Profiles page
2. Click the download icon on a profile
3. Profile is saved as JSON file

#### Import a Profile

1. Go to Profiles page
2. Click "Import Profile"
3. Select the JSON file
4. Profile will be imported with a new ID

### Duplicating Profiles

Create a copy of an existing profile:

1. Go to Profiles page
2. Click the copy icon on a profile
3. A duplicate is created with "(Copy)" suffix

## Tips and Tricks

### Organizing Your Deck

- **Group by Purpose**: Keep related buttons together
- **Use Multiple Pages**: Don't overcrowd a single page
- **Color Code**: Use custom colors for different types of actions
- **Consistent Icons**: Use similar icons for related actions

### Efficiency Tips

- **Multi-Actions**: Combine frequently used actions
- **Keyboard Shortcuts**: Use hotkey actions for common shortcuts
- **Profile Switching**: Create profiles for different tasks
- **Recent Actions**: Check Settings for recently used actions

### Touch Screen Optimization

- **Larger Buttons**: Use button size slider in Settings
- **Swipe Navigation**: Swipe left/right to change pages
- **Clear Labels**: Keep labels short and readable

### Desktop App Features

- **System Tray**: Minimize to tray instead of closing
- **Global Hotkey**: Press Ctrl+Shift+D to show/hide deck
- **Always on Top**: Keep deck above other windows
- **Auto-Start**: Launch VDock when Windows starts

### Keyboard Shortcuts

- `Ctrl+E`: Toggle edit mode
- `Ctrl+S`: Save profile
- `Ctrl+Z`: Undo
- `Ctrl+Y`: Redo
- `Ctrl+,`: Settings

### Best Practices

1. **Save Often**: Click Save regularly when editing
2. **Test Actions**: Test new actions before relying on them
3. **Backup Profiles**: Export important profiles regularly
4. **Meaningful Names**: Use descriptive button labels
5. **Tooltips**: Add tooltips for clarity

### Common Issues

#### Button doesn't work
- Check that action is configured correctly
- Verify paths for program/command actions
- Test the action manually first

#### Can't find an icon
- Use the Icon Picker to browse
- Search by name
- Upload a custom icon

#### Layout looks wrong
- Check grid configuration
- Verify button positions don't overlap
- Adjust button sizes

## Getting Help

- Check the [README.md](../README.md) for technical information
- Review [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) for advanced features
- Report issues on GitHub
- Join the community Discord (coming soon)

## Next Steps

- Explore the plugin system for advanced integrations
- Create profiles for different workflows
- Share your profiles with the community
- Contribute to VDock development

Happy decking! 🎮

