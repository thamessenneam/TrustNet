# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['setup_wizard.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['trustnet.core', 'trustnet.network.node', 'trustnet.network.ledger', 'trustnet.network.client', 'trustnet.network.discovery', 'trustnet.network.protocol', 'zeroconf', 'cryptography.hazmat.primitives.asymmetric.ed25519'],
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
    name='TrustNet-Setup',
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
