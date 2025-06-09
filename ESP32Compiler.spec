# ESP32Compiler.spec
# Arquivo de configuração para PyInstaller

import os

block_cipher = None

# Dados adicionais a serem incluídos
added_files = []

# Se existir um ícone, incluir
if os.path.exists('esp32.ico'):
    icon_path = 'esp32.ico'
else:
    icon_path = None

a = Analysis(
    ['esp32_compiler_embedded.py'],  # Script principal com firmware embutido
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'serial',
        'serial.tools.list_ports',
        'base64',
        'tempfile',
        'subprocess',
        'time',
        'esptool',
        'esptool.cmds',
        'esptool.loader',
        'esptool.util'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2'
    ],
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
    name='ESP32AutoFlasher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compressão UPX para arquivo menor
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Interface de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    version_file='version_info.txt'  # Arquivo de versão (opcional)
)