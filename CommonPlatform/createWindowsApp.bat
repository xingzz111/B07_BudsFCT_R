@echo off

echo "-------------------- CreateApp Start --------------------"

set cPath=%~d0
set filePath=%~p0 
set filePath=%cPath%%filePath%
echo current path: %filePath%

if exist .\OSENSTester (
    rmdir /Q /S .\OSENSTester
)
if exist .\dist (
    rmdir /Q /S .\dist
)
if exist .\build (
    rmdir /Q /S .\build
)
if exist .\__pycache__ (
    rmdir /Q /S .\__pycache__
)

pyinstaller .\src\spec\Tester_windows.spec


xcopy D:\Overlay\CommonPlatform\src\configure\*.json .\dist\configure\ /E /I
xcopy D:\Overlay\engine .\dist\engine\ /E /I
xcopy D:\Overlay\engine\profile\*.csv .\dist\profile\ /E /I
.\src\signer\signer_win.exe -d .\dist
rmdir /Q /S .\build
move .\dist .\OSENSTester
xcopy .\killport.bat .\OSENSTester
xcopy .\__init__.py .\OSENSTester

echo "-------------------- CreateApp End ----------------------"
pause
