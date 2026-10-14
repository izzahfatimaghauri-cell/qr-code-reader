# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['qrreaderr.py'],
    pathex=[],
    binaries=[
        (r'C:\Users\prime pc\PycharmProjects\QRreader\venv\Lib\site-packages\pyzbar\libiconv-2.dll', '.'),
        (r'C:\Users\prime pc\PycharmProjects\QRreader\venv\Lib\site-packages\pyzbar\libzbar-32.dll', '.'),
    ],
    datas=[],
    hiddenimports=[],
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
    name='QRReader',
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
)