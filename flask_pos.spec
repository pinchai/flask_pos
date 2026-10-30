# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('migrations', 'migrations'),
]

# Collect reportlab resources for PDF invoice generation
reportlab_datas, reportlab_binaries, reportlab_hiddenimports = collect_all('reportlab')
datas += reportlab_datas

hiddenimports = [
    'waitress',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.sql.default_comparator',
    'models',
    'config',
    'extensions',
    'seed',
    'backup',
    'blueprints',
    'blueprints.dashboard',
    'blueprints.dashboard.routes',
    'openpyxl',
    'requests',
    'dotenv',
] + reportlab_hiddenimports

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=reportlab_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['flask_restx', 'flask_jwt_extended'],
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
    name='flask_pos',
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
