@echo off

echo "---------------------------------Starting---------------------------------------------"

set basepath=%~dp0..
set PYTHONPATH=D:\\Overlay

set launcher=C:\\Python\\Lib\\site-packages\\rtSque\\lynx\\launcher

set BASE_PATH=%PYTHONPATH%\\engine
set DRIVER_FOLDER=%BASE_PATH%\\driver
set ADDON_DRIVER_FOLDER=%BASE_PATH%\\addon\\driver

set PROFILE_FOLDER=%BASE_PATH%\\addon\\config
set HW_PROFILE=%PROFILE_FOLDER%\\hw_profile.json
set SW_PROFILE=%PROFILE_FOLDER%\\sw_profile.json


C:\\Python\\python.exe "%launcher%\\launcher.py" -p "%HW_PROFILE%" -s "%SW_PROFILE%" --driver_folder="%DRIVER_FOLDER%" --driver_folder="%ADDON_DRIVER_FOLDER%"
pause