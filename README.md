# Windows Application Time Tracker (TokiKanri)

This is a time-tracking application for Windows that allows you to monitor the time you spend on different programs.

## Download

You can download the latest version of TokiKanri from the [Releases section](https://github.com/niiccnm/TokiKanri/releases) of the repository.

## What it does

The application tracks the active window on your desktop and records the time spent on each program. It provides a user-friendly interface to view and manage the tracked applications.

## Features

- **Application Time Tracking**: Automatically tracks the time spent on different applications.
- **Window Selection**: Allows you to select a specific window to track.
- **Main and Mini Views**: A main window provides a detailed view of all tracked programs, while a mini-window offers a compact, always-on-top view of the currently tracked application.
- **System Tray Integration**: The application can be minimized to the system tray for unobtrusive operation.
- **Activity-Based Tracking**: Automatically pauses the timer when no user activity is detected.
- **Custom Display Names**: Rename tracked programs with custom display names that persist across application restarts.
- **Media Mode**: Tracks window activity for media players without requiring user input, perfect for watching videos or listening to music.
- **Media Playback Detection**: Optionally only tracks time when media is actually playing, using Windows Media Control API.
- **Customizable Media Programs**: Add or remove programs that should be considered media players for Media Mode.
- **Automatic Updates**: Checks for new versions at startup and provides the option to manually check for updates in the Settings window.
- **Responsive Layout**: The main window adapts to different sizes, showing essential controls when minimized.
- **Windows Notifications**: Receives toast notifications for media API failures and recovery.
- **Timer Controls**: You can reset timers for individual programs or for all tracked programs at once.
- **Program Management**: Add new programs to the tracking list or remove existing ones.
- **Always on Top**: Pin the window to keep it visible over other applications.
- **Persistent Data**: The application saves your tracking data, so your progress is not lost when you close it.
- **Dark Mode**: Toggle between light and dark themes for comfortable usage in different lighting conditions.
- **Search Functionality**: Filter tracked programs to quickly find specific applications.
- **Settings Window**: Configure application behavior including:
  - Maximum number of programs to track
  - Dark mode toggle
  - Mini-window startup option
  - Windows startup integration
  - Media mode for tracking without user input
  - Customize media programs list
  - Check for updates manually
- **Import/Export**: Save and load your tracking data and configuration settings.

## Requirements

To run this application, you will need the following:

- Python 3.6 or higher
- The following Python packages:
  - `pywin32` (version 305 or higher)
  - `psutil` (version 5.9.0 or higher)
  - `pillow` (version 10.0 or higher) for system tray icons
  - `winsdk` (version 1.0.0b7 or higher) for media playback detection
  - `windows-toasts` (version 1.3.0 or higher) for Windows toast notifications

You can install the required packages using pip:

```bash
pip install -r requirements.txt
```

## How to Run

To start the application, run the `main.py` script:

```bash
python main.py
```

## Using the Application

### Main Window
- **Select Window to Track**: Click this button, then click on any window to start tracking it.
- **Reset All Timers**: Reset the time for all tracked applications.
- **Remove All**: Remove all tracked programs from the list.
- **Pin Button**: Keep the window on top of other applications.
- **Minimize Button**: Minimize to the mini-window view.
- **Settings Button**: Open the settings window.
- **Search Bar**: Filter tracked programs by name.
- **Custom Names**: Hover over a program name to reveal the edit button, allowing you to set a custom display name.

### Mini Window
- **Double-click**: Switch to the main window view.
- **Right-click**: Open a context menu with options to show the main window or exit.
- **Drag**: Move the mini-window to a different position on the screen.

### Settings Window
- **Max Programs to Track**: Set the maximum number of programs that can be tracked.
- **Start at Windows Startup**: Launch the application automatically when Windows starts.
- **Start in Mini-Window Mode**: Start the application in the compact mini-window view.
- **Media Mode**: Enable tracking for media players without requiring user input.
- **Media Programs**: Add or remove programs that should be considered media players.
- **Require Media Playback**: Only track time for media programs when media is actually playing.
- **Dark Mode**: Toggle between light and dark themes.
- **Check for Updates**: Manually check for new versions of the application.
- **Media API Status**: Shows the current status of the Windows Media Control API.

### Media Mode
Media Mode is designed for tracking time spent watching videos or listening to music. When enabled:
- The application will continue tracking time for supported media players even if there's no keyboard or mouse activity
- Default supported players include: VLC, mpv, MPC-HC, MPC-BE, PotPlayer, MusicBee, and Spotify
- You can customize the list of media programs in the Settings window
- Process name detection is case-insensitive and works with or without the .exe extension
- Perfect for accurately tracking time spent consuming media content
- Optional playback detection ensures time is only tracked when media is actually playing
- Uses Windows Media Control API to detect if media is playing, paused, or stopped

For detailed setup instructions for all supported media players, see the [Media-Playback-Setup.md](Media-Playback-Setup.md) guide.

## Data Files
- **program_tracker_data.json**: Contains tracked program data.
- **tokikanri_config.json**: Contains application settings.
- **logs/tokikanri.log**: Contains application logs.

## Creating an Executable

You can convert the Python application into a standalone Windows executable using `PyInstaller`.

First, make sure you have `PyInstaller` installed:

```bash
pip install pyinstaller
```

Then, run the following command in the project's root directory to build the executable using the provided spec file:

```bash
pyinstaller TokiKanri.spec
```

The final executable will be located in the `dist` directory.

## Version History

For a detailed list of changes in each version, please see the [CHANGELOG.md](CHANGELOG.md) file.

Current version: 0.0.3 (2025-07-14)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
