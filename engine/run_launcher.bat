@echo off

echo "---------------------------------Starting---------------------------------------------"

set basepath=%~dp0
echo current path: %basepath%
set PYTHONPATH=%basepath:~0, -8%
REM Put packaged dependencies ahead of system site-packages (fix pyzmq/zmq import)
set PYTHONPATH=C:\site-packages;%PYTHONPATH%

set launcher=C:\Python\Lib\site-packages\rtSque\lynx\launcher

set BASE_PATH=%basepath:~0, -1%
set DRIVER_FOLDER=%BASE_PATH%\driver
set ADDON_DRIVER_FOLDER=%BASE_PATH%\addon\driver

echo python path: %PYTHONPATH%
echo base path: %BASE_PATH%
echo driver path: %DRIVER_FOLDER%
echo addon driver path: %ADDON_DRIVER_FOLDER%

set PROFILE_FOLDER=%BASE_PATH%\addon\config
set HW_PROFILE=%PROFILE_FOLDER%\hw_profile.json
set SW_PROFILE=%PROFILE_FOLDER%\sw_profile.json


C:\Python\python.exe "%launcher%\launcher.py" -p "%HW_PROFILE%" -s "%SW_PROFILE%" --driver_folder="%DRIVER_FOLDER%" --driver_folder="%ADDON_DRIVER_FOLDER%"
pause