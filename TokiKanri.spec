# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import site

# Try to locate winsdk module
winsdk_path = None
for path in site.getsitepackages():
    potential_path = os.path.join(path, 'winsdk')
    if os.path.exists(potential_path):
        winsdk_path = potential_path
        break

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('program_tracker.py', '.'),
        ('main_window.py', '.'),
        ('mini_window.py', '.'),
        ('program_gui.py', '.'),
        ('activity_tracker.py', '.'),
        ('data_manager.py', '.'),
        ('window_selector.py', '.'),
        ('system_tray.py', '.'),
        ('ui_components.py', '.'),
        ('utils.py', '.'),
        ('config.py', '.'),
        ('logger.py', '.')
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'win32gui',
        'win32process',
        'win32api',
        'win32con',
        'psutil',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'pystray',
        'logging',
        'logging.handlers',
        'winsdk',
        'winsdk.windows',
        'winsdk.windows.media',
        'winsdk.windows.media.control'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add winsdk files if they exist
if winsdk_path:
    print(f"Found winsdk at: {winsdk_path}")
    
    # Add all winsdk DLLs as binaries
    for root, dirs, files in os.walk(winsdk_path):
        for file in files:
            if file.endswith('.dll') or file.endswith('.pyd'):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, winsdk_path)
                target_dir = os.path.join('winsdk', os.path.dirname(relative_path))
                a.binaries.append((os.path.join(target_dir, file), full_path, 'BINARY'))

    # Add all winsdk data files
    for root, dirs, files in os.walk(winsdk_path):
        for file in files:
            if not (file.endswith('.dll') or file.endswith('.pyd') or file.endswith('.py') or file.endswith('.pyc')):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, winsdk_path)
                target_dir = os.path.join('winsdk', os.path.dirname(relative_path))
                a.datas.append((os.path.join(target_dir, file), full_path, 'DATA'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TokiKanri',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version.txt',
)
