@echo off
chcp 65001 >nul
echo ========================================
echo   Calibration Tool GUI Packaging Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.7+
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [Info] Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [Error] PyInstaller installation failed
        pause
        exit /b 1
    )
)

REM Check if PySide6 is installed
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo [Info] Installing PySide6...
    pip install PySide6
    if errorlevel 1 (
        echo [Error] PySide6 installation failed
        pause
        exit /b 1
    )
)

REM Check if pyserial is installed
python -c "import serial" >nul 2>&1
if errorlevel 1 (
    echo [Info] Installing pyserial...
    pip install pyserial
    if errorlevel 1 (
        echo [Error] pyserial installation failed
        pause
        exit /b 1
    )
)

echo [Info] All dependency checks passed, starting packaging...
echo.

REM Create PyInstaller spec file (if advanced configuration needed)
echo [Info] Generating packaging configuration...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis(
echo     ['calibration_gui.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[],
echo     hiddenimports=[],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo )
echo.
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
echo.
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     name='calibration_gui',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     runtime_tmpdir=None,
echo     console=False,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo )
) > calibration_gui.spec

REM Use PyInstaller for packaging
echo [Info] Starting GUI application packaging...
pyinstaller --onefile --windowed --name="CalibrationTool" --icon=icon.png calibration_gui.py

if errorlevel 1 (
    echo [Error] Packaging failed, please check error messages
    pause
    exit /b 1
)

echo.
echo [Success] Packaging completed!
echo.
echo Generated file location:
echo   - dist\\CalibrationTool.exe
echo.
echo You can:
echo   1. Run dist\\CalibrationTool.exe directly
echo   2. Copy dist folder to other Windows computers
echo   3. No Python environment required to run
echo.

REM Clean up temporary files (optional)
echo [Info] Cleaning up temporary files...
del calibration_gui.spec >nul 2>&1
rd /s /q build >nul 2>&1

echo.
echo ========================================
echo   Packaging completed! Press any key to exit...
echo ========================================
pause