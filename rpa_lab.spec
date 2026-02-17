# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para RPA Lab
"""
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        ('src', 'src'),
    ],
    hiddenimports=[
        # GUI
        'customtkinter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        # Database
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        # Scheduling
        'apscheduler',
        'apscheduler.schedulers.background',
        'apscheduler.triggers.cron',
        'apscheduler.triggers.interval',
        'apscheduler.triggers.date',
        # Utils
        'pyyaml',
        'yaml',
        'loguru',
        'pydantic',
        'dotenv',
        'python_dotenv',
        # RPA
        'pyautogui',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'mouse',
        'keyboard',
        'pyperclip',
        'psutil',
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
    name='RPA-Lab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # False = sem janela de terminal (modo GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,          # Adicione um .ico aqui se quiser ícone personalizado
)
