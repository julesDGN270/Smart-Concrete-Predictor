# -*- mode: python ; coding: utf-8 -*-
# Genere l'executable Windows a partir de app_v2.py.
# Usage (sur Windows, ou via le workflow GitHub Actions build-windows.yml) :
#     pip install -r requirements.txt pyinstaller
#     pyinstaller build_windows.spec
# Le resultat se trouve dans dist/SmartConcretePredictor/

block_cipher = None

a = Analysis(
    ['app_v2.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('best_concrete_model.pkl', '.'),
    ],
    hiddenimports=[
        'catboost', 'lightgbm', 'xgboost', 'sklearn',
        'reportlab.graphics.barcode',
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
    [],
    exclude_binaries=True,
    name='SmartConcretePredictor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SmartConcretePredictor',
)
