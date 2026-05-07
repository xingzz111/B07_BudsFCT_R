#!/bin/bash

basepath=$(cd `dirname $0`;cd ..;pwd)
export PYTHONPATH=/Users/prm0469/Downloads/engine-master/src/
# export PYTHONPATH=$PYTHONPATH:$basepath
cd `dirname $0`
cd ..

launcher=/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/rtSque/lynx/launcher

# load driver from 2 folders:
# /mix/driver is module vendor driver, including
#    lynx-core-driver
#    other vendor's module/ic/ipcore driver.
# /mix/addon/driver is station specific drivers
#    mostly station base-board driver.
BASE_PATH=$PYTHONPATH/engine
DRIVER_FOLDER=$BASE_PATH/driver
ADDON_DRIVER_FOLDER=$BASE_PATH/addon/driver/

PROFILE_FOLDER=$BASE_PATH/addon/config/
HW_PROFILE=$PROFILE_FOLDER/hw_profile.json
SW_PROFILE=$PROFILE_FOLDER/sw_profile.json
# support both profile.json and hw+sw profile.
if [ -f $HW_PROFILE ]
then
    /Library/Frameworks/Python.framework/Versions/3.9/bin/python3 $launcher/launcher.py -p $HW_PROFILE -s $SW_PROFILE --driver_folder=$DRIVER_FOLDER --driver_folder=$ADDON_DRIVER_FOLDER
else
    echo 'Hardware profile (hw_profile.json) is not found in '$PROFILE_FOLDER'; launcher cannot run without hardware config file.'
fi
