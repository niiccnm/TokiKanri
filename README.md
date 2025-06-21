# Windows Application Time Tracker (TokiKanri)

This is a time-tracking application for Windows that allows you to monitor the time you spend on different programs.

## What it does

The application tracks the active window on your desktop and records the time spent on each program. It provides a user-friendly interface to view and manage the tracked applications.

## Features

- **Application Time Tracking**: Automatically tracks the time spent on different applications.
- **Window Selection**: Allows you to select a specific window to track.
- **Main and Mini Views**: A main window provides a detailed view of all tracked programs, while a mini-window offers a compact, always-on-top view of the currently tracked application.
- **System Tray Integration**: The application can be minimized to the system tray for unobtrusive operation.
- **Activity-Based Tracking**: Automatically pauses the timer when no user activity is detected.
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
- **Import/Export**: Save and load your tracking data and configuration settings.

## Requirements

To run this application, you will need the following:

- Python 3.6 or higher
- The following Python packages:
  - `pywin32` (version 303 or higher)
  - `psutil` (version 5.9.0 or higher)
  - `pillow` (version 9.0.0 or higher) for system tray icons

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

### Mini Window
- **Double-click**: Switch to the main window view.
- **Right-click**: Open a context menu with options to show the main window or exit.
- **Drag**: Move the mini-window to a different position on the screen.

### Settings Window
- **Max Programs to Track**: Set the maximum number of programs that can be tracked.
- **Start at Windows Startup**: Launch the application automatically when Windows starts.
- **Start in Mini-Window Mode**: Start the application in the compact mini-window view.
- **Dark Mode**: Toggle between light and dark themes.

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.
