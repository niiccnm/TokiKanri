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

## [0.0.2] - 2025-06-21
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

## [0.0.1] - 2025-06-20

### Added
- Initial project setup and basic features.