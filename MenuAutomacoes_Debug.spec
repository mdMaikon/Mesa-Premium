# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['menu_principal.py'],
    pathex=[],
    binaries=[],
    datas=[('configs', 'configs'), ('automacoes', 'automacoes'), ('.env.template', '.')],
    hiddenimports=['mysql.connector', 'selenium', 'customtkinter', 'cqrs_commands', 'cqrs_queries', 'cqrs_handlers', 'cqrs_mediator', 'di_container', 'service_registry'],
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
    name='MenuAutomacoes_Debug',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
