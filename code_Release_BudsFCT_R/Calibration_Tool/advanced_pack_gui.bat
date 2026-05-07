@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   Advanced Calibration Tool GUI Packaging Script
echo ========================================
echo.

REM Set variables
set "PROJECT_DIR=%~dp0"
set "DIST_DIR=%PROJECT_DIR%dist"
set "BUILD_DIR=%PROJECT_DIR%build"
set "EXE_NAME=校准工具"
set "MAIN_FILE=calibration_gui.py"

REM Check if running in project directory
if not exist "%MAIN_FILE%" (
    echo [Error] Please run this script in the project root directory
    echo Current directory: %PROJECT_DIR%
    pause
    exit /b 1
)

REM Display system information
echo [Info] System Information:
echo   Project Directory: %PROJECT_DIR%
echo   Target File: %MAIN_FILE%
echo   Output Name: %EXE_NAME%
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.7+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo [Info] Detected: %PYTHON_VERSION%

REM Check dependencies
set "MISSING_PACKAGES="

python -c "import PySide6" >nul 2>&1
if errorlevel 1 set "MISSING_PACKAGES=%MISSING_PACKAGES% PySide6"

python -c "import serial" >nul 2>&1
if errorlevel 1 set "MISSING_PACKAGES=%MISSING_PACKAGES% pyserial"

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 set "MISSING_PACKAGES=%MISSING_PACKAGES% pyinstaller"

REM Install missing packages
if not "%MISSING_PACKAGES%"=="" (
    echo [Info] Need to install the following packages: %MISSING_PACKAGES%
    echo.
    
    for %%p in (%MISSING_PACKAGES%) do (
        echo [Installing] Installing %%p...
        pip install %%p --user
        if errorlevel 1 (
            echo [Error] %%p installation failed
            pause
            exit /b 1
        )
    )
    echo.
)

echo [Info] All dependency checks passed
echo.

REM Create advanced spec file
echo [Info] Creating advanced packaging configuration...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo import sys

echo block_cipher = None
echo.
echo # Add data files
echo added_files = [
echo     ('calibration_functions.py', '.', 'DATA'),
echo     ('custom_calibrations.json', '.', 'DATA'),
echo ]
echo.
echo a = Analysis(
echo     ['calibration_gui.py'],
echo     pathex=[sys._MEIPASS],
echo     binaries=[],
echo     datas=added_files,
echo     hiddenimports=[
echo         'PySide6.QtWidgets',
echo         'PySide6.QtCore',
echo         'PySide6.QtGui',
echo         'serial',
echo         'serial.tools.list_ports',
echo         'calibration_functions',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=['tkinter'],
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
echo     [],
echo     exclude_binaries=True,
echo     name='%EXE_NAME%',
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
echo     icon='icon.png',
echo )
) > calibration_gui_advanced.spec

REM Execute packaging
echo [Info] Starting packaging process...
echo This may take a few minutes, please wait patiently...
echo.

pyinstaller calibration_gui_advanced.spec

if errorlevel 1 (
    echo [Error] Packaging failed
    echo Please check the error messages above
    pause
    exit /b 1
)

REM Check generated executable file
if exist "%DIST_DIR%\%EXE_NAME%.exe" (
    echo [Success] Executable file generated: %DIST_DIR%\%EXE_NAME%.exe
    
    REM Display file size
    for /f %%i in ('"%DIST_DIR%\%EXE_NAME%.exe"') do set "FILE_SIZE=%%~zi"
    set /a "FILE_SIZE_MB=!FILE_SIZE!/1048576"
    echo [Info] File size: !FILE_SIZE_MB! MB
    
    REM Create startup script
    echo @echo off > "%DIST_DIR%\StartCalibrationTool.bat"
    echo chcp 65001 >> "%DIST_DIR%\StartCalibrationTool.bat"
    echo echo Starting calibration tool... >> "%DIST_DIR%\StartCalibrationTool.bat"
    echo "%EXE_NAME%.exe" >> "%DIST_DIR%\StartCalibrationTool.bat"
    echo pause >> "%DIST_DIR%\StartCalibrationTool.bat"
    
    echo [Info] Startup script created: %DIST_DIR%\StartCalibrationTool.bat
    
) else (
    echo [Error] Executable file generation failed
    pause
    exit /b 1
)

REM Clean up temporary files
echo.
echo [Info] Cleaning up temporary files...
del calibration_gui_advanced.spec >nul 2>&1

REM Ask if clean build directory
set /p "CLEAN_BUILD=Clean build temporary directory? (y/n, default n): "
if /i "!CLEAN_BUILD!"=="y" (
    rd /s /q "%BUILD_DIR%" >nul 2>&1
    echo [Info] Build directory cleaned
)

echo.
echo ========================================
echo   Packaging Completed!
echo ========================================
echo.
echo Generated files:
echo   - %DIST_DIR%\%EXE_NAME%.exe (Main program)
echo   - %DIST_DIR%\StartCalibrationTool.bat (Startup script)
echo.
echo Usage instructions:
echo   1. Copy the entire dist folder to target computer
echo   2. Double-click "StartCalibrationTool.bat" or run exe file directly
echo   3. No Python environment required
echo   4. Supports Windows 7/8/10/11 systems
echo.
echo Notes:
echo   - First run may take a few seconds to load
echo   - Ensure target computer has .NET Framework 4.5+
echo   - Install appropriate drivers for serial port functionality
echo.
REM Ask if test run
set /p "TEST_RUN=Test run now? (y/n, default n): "
if /i "!TEST_RUN!"=="y" (
    echo [Info] Starting test...
    timeout /t 2 >nul
    "%DIST_DIR%\%EXE_NAME%.exe"
)

echo.
echo Press any key to exit...
pause >nul