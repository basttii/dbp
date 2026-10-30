# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['dbp_cleaner.py'],
    pathex=[],
    binaries=[],
    datas=[('besen.ico', '.')],
    hiddenimports=[
        'dbp_core',
        'dbp_core.constants',
        'dbp_core.i18n',
        'dbp_core.config',
        'dbp_core.smart_trash',
        'dbp_core.cleaner',
        'dbp_core.system',
        'dbp_core.gui_config',
        'dbp_core.gui_portable',
        'dbp_core.main',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='dbp_cleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['besen.ico'],
)
