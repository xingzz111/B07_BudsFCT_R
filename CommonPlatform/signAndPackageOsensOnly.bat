@echo off
setlocal
cd /d "%~dp0"

echo -------------------- Package+Sign Only (no PyInstaller) --------------------

REM Prebuilt GUI exe: %%1 optional full path; else .\UI.exe; else ..\OSENSTester.exe
set "SRC_EXE="
if not "%~1"=="" (
  set "SRC_EXE=%~f1"
) else if exist ".\UI.exe" (
  set "SRC_EXE=%~dp0UI.exe"
) else if exist "..\OSENSTester.exe" (
  set "SRC_EXE=%~dp0..\OSENSTester.exe"
)

if "%SRC_EXE%"=="" (
  echo ERROR: No prebuilt exe. Use one of:
  echo   - Pass path as %%1 ^(e.g. signAndPackageOsensOnly.bat C:\build\MyUI.exe^)
  echo   - Place UI.exe beside this bat
  echo   - Place OSENSTester.exe one level above this folder ^(Overlay\ layout^)
  exit /b 1
)

if not exist "%SRC_EXE%" (
  echo ERROR: Source exe not found: %SRC_EXE%
  exit /b 1
)

if exist .\OSENSTester (
    rmdir /Q /S .\OSENSTester
)
if exist .\dist (
    rmdir /Q /S .\dist
)

mkdir .\dist 2>nul
copy /Y "%SRC_EXE%" ".\dist\OSENSTester.exe"
if errorlevel 1 (
  echo ERROR: Copy to dist\OSENSTester.exe failed
  exit /b 1
)

mkdir .\dist\configure 2>nul
mkdir .\dist\profile 2>nul
mkdir .\dist\engine 2>nul
xcopy ".\src\configure\*.json" ".\dist\configure\" /E /I /Y
if errorlevel 4 (
  echo ERROR: Missing configure JSON under .\src\configure\
  exit /b 1
)

xcopy "..\engine" ".\dist\engine\" /E /I /Y
if errorlevel 4 (
  echo ERROR: xcopy ..\engine failed
  exit /b 1
)

for %%F in ("..\engine\profile\*.csv") do copy /Y "%%~fF" ".\dist\profile\" 2>nul

.\src\signer\signer_win.exe -d .\dist
if errorlevel 1 (
  echo ERROR: signer_win.exe failed
  exit /b 1
)

if exist .\build rmdir /Q /S .\build
move .\dist .\OSENSTester

copy /Y .\killport.bat .\OSENSTester\
copy /Y .\__init__.py .\OSENSTester\

echo -------------------- Package+Sign Only End ----------------------

endlocal
exit /b 0
