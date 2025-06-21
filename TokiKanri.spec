# -*- mode: python ; coding: utf-8 -*-

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
        'logging.handlers'
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
