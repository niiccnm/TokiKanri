# Media Playback Detection Setup Guide

This guide explains how to properly configure media players to work with TokiKanri's Media Mode playback detection feature.

## Introduction

TokiKanri can detect when media is actually playing in supported applications by using the Windows Media Control API (also known as SMTC - System Media Transport Controls). This ensures that time is only tracked when you're actively watching or listening to content.

## Supported Media Players

The following media players are supported by TokiKanri's playback detection:

| Application | Setup Required | Instructions |
|------------|----------------|--------------|
| VLC Media Player | Yes | See below |
| mpv | No | Works out of the box |
| MPC-HC | Yes | See below  |
| MPC-BE | Yes | See below  |
| PotPlayer | No | Works out of the box |
| MusicBee | No | Works out of the box |
| Spotify | No | Works out of the box |

## VLC Media Player Setup

VLC requires a plugin to integrate with Windows Media Controls:

1. Download the plugin from: https://github.com/spmn/vlc-win10smtc/releases
2. Copy the `libwin10smtc_plugin.dll` file to your VLC plugins directory:
   * Typically: `C:\Program Files\VideoLAN\VLC\plugins\misc\`
   * Note: Make sure to use the correct version (x86 or x64) that matches your VLC installation
3. Restart VLC
4. In VLC, go to: 
   * Tools > Preferences
   * Click on "All" at the bottom to show advanced preferences
   * Navigate to Interface > Control Interfaces
   * Check "Windows 10 SMTC integration"
   * Click "Save"
5. Restart VLC again

## MPC-HC Setup

To enable Windows Media Controls integration in Media Player Classic - Home Cinema:

1. Open MPC-HC
2. Go to Options (or press the "O" key)
3. Select the "Player" section
4. Click on "User Interface"
5. Check the option "Control via Windows UI (SMTC)"
6. Click "Apply" and "OK"
7. Restart MPC-HC

## MPC-BE Setup

To enable Windows Media Controls integration in Media Player Classic - Black Edition:

1. Open MPC-BE
2. Go to Options (or press the "O" key)
3. Select the "Miscellaneous" section
4. Check the option "Use Window Media Controls"
5. Click "Apply" and "OK"
6. Restart MPC-BE

## Troubleshooting

If playback detection isn't working properly:

1. **Verify Media Mode is enabled** - Go to TokiKanri Settings and make sure both "Media Mode" and "Require Media Playback" are checked.

2. **Check your media player version** - Make sure you're using a recent version of your media player.

3. **VLC specific** - Ensure you've followed all VLC setup steps correctly and are using the right version of the plugin (x86 or x64).

4. **System permissions** - Make sure TokiKanri has the necessary permissions to access media information.

5. **Windows Media Settings** - Check your Windows settings:
   * Go to Windows Settings > Privacy > Media playback
   * Ensure "Let Windows and apps use my playback information" is turned on

## Adding Custom Media Players

If you want to add your own media players to the list:

1. Go to TokiKanri Settings
2. Find the "Media Programs" section
3. Click "Add" and enter the process name of your media player (with or without .exe)

Note that playback detection will only work if the media player supports the Windows Media Controls API. 