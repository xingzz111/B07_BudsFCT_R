# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

info_plist = {
    "CFBundleName": "PRMTester",
    "CFBundleDisplayName": "PRMTester",
    "CFBundleGetInfoString": "",
    "CFBundleIdentifier": "",
    "CFBundleVersion": "1.0.1",
    "CFBundleShortVersionString": "1.0.1",
    "NSHumanReadableCopyright": u"Copyright © 2024, Zcnwei, All Rights Reserved",
    "NSHighResolutionCapable": True,
    "NSPrincipalClass": 'NSApplication'
}

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[],
    datas=[('../gui/img', 'img')],
    hiddenimports=[],
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
    name='PRMTester',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity="",
    entitlements_file=None,
    icon=['../gui/img/AppIcon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas, 
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PRMTester'
)
app = BUNDLE(
    coll,
    upx=True,
    upx_exclude=[],
    name='PRMTester.app',
    icon='../gui/img/AppIcon.icns',
    info_plist=info_plist,
    bundle_identifier='PRM-BUA-SW-Team',
)
