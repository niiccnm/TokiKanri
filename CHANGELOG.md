# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added
- New features or functionality

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Vulnerability fixes

---

## [v0.0.3] - 2025-07-14

### Added
- Automatic update checker to detect new versions from GitHub releases
  - Checks for updates at application startup
  - Manual "Check for Updates" button added to Settings window
  - Displays release notes when updates are available
- Windows Media Control API status monitoring in settings window
- Windows toast notifications for media API failures and recovery

### Changed
- Improved main window layout to work better in minimized state:
  - Implemented responsive layout that adapts to window size
  - Added compact button arrangement in minimized mode showing essential functions
  - Reorganized controls to ensure all important buttons remain accessible
- Standardized all docstrings to use Google format for improved code readability and documentation consistency
- Improved "Add Media Program" dialog UI:
  - Created "Add" and "Cancel" buttons
  - Widened input field to better utilize available space
  - Improved button positioning and layout
  - Enhanced spacing and padding for better visual balance
  - Simplified label text for better clarity
- Replaced win10toast with Windows-Toasts package for notifications to fix deprecated dependency warnings

### Fixed
- Fixed blocking operations in GUI thread in program_tracker.py
  - Added ThreadManager class to handle background tasks
  - Moved media detection to background threads to prevent UI freezing
  - Moved file operations (import/export) to background threads
  - Moved active window detection to background threads
  - Added proper result handling and callback mechanism for thread operations
- Converted global state (_last_logged_process) in ActivityTracker to instance variables to prevent race conditions in multi-instance scenarios
- Fixed potential memory leaks in media tracking by reducing polling frequency and improving resource cleanup
- Added timeout mechanism to Windows Media Control API calls to prevent application hanging
- Fixed issue where scrolling in media programs list would also scroll the tracked programs list
  - Improved mousewheel event binding to only affect the intended scrollable area
  - Added proper event propagation control to prevent unintended scrolling behavior
- Implemented non-blocking approach for media detection to improve application stability
- Fixed memory leaks in the Windows Media Control API integration with proper resource cleanup
  - Added explicit cleanup of Windows Media API objects
  - Improved async/await patterns with proper task cancellation and cleanup
  - Reused ThreadPoolExecutor to prevent creating new executors on each check
  - Added event loop management to prevent lingering event loops
  - Implemented explicit resource cleanup on application shutdown

---

## [v0.0.2] - 2025-06-21
### Added
- Custom display names for tracked programs with hover-activated edit button
  - Styled editing dialog with "Reset to Default" option
  - Names persist across application restarts
- Media Mode feature for effortless tracking during media consumption without requiring user input
  - Supports media players (VLC, mpv, MPC-HC/BE, PotPlayer) and music apps (MusicBee, Spotify)
  - Configurable through Settings with customizable program list
  - Optional playback detection using Windows Media Control API to only track active playback
  - Controlled via dedicated Settings toggles
  - Added detailed Media Playback Setup guide (media_playback_setup.md) for configuring supported players
- Clear button (X) in search bar to quickly clear search text

### Changed
- Improved console logging with cleaner, more focused output
- Implemented a centralized Config class to ensure consistent configuration across the application

### Fixed
- Enhanced config file saving with temporary file approach to prevent corruption
- Improved settings persistence and proper saving at startup
- Better edit icon appearance and sizing for improved visibility
- Search results now persist during timer data refreshes
- Program reorganization feature optimized to maintain proper sorting by time spent
- Improved sorting algorithm performance and consistent program ordering during updates
- Eliminated duplicate log messages and reduced console clutter
- Fixed focus management in search bar to properly release focus when clicking elsewhere
- Adjusted log levels to prioritize important information while moving detailed debugging to debug level
- Fixed visual bug with white/gray bar appearing above program timers


---

## [v0.0.1] - 2025-06-20

### Added
- Initial project setup and basic features.