#!/bin/bash

sudo true

BasePath=$(cd "$(dirname "$0")";pwd)

AppName="OSSNSTester"
Comment="OSSNSTester Application"
ExecPath="$BasePath/OSSNSTester"
IconPath="$BasePath/img/icon.png"

DesktopEntryPath="$HOME/.local/share/applications/$AppName.desktop"
LinkPath="$HOME/Desktop/OSSNSTester"

if [ ! -f "$ExecPath" ]; then
	echo "!!!!!!!!!!!!!!!!!! Not PRMTester!!!!!!!!!!!!!!!!!!"
	exit 1
fi

if [ ! -x "$ExecPath" ]; then
  chmod 777 $ExecPath
fi

if [ ! -f "$IconPath" ]; then
  echo "!!!!!!!!!!!!!!!!!! Not Icon !!!!!!!!!!!!!!!!!!"
  exit 1
fi

if [ -f "$LinkPath" ]; then
  rm -rf $LinkPath
fi

if [ -f "$DesktopEntryPath" ]; then
  rm -rf $DesktopEntryPath
fi

cat > "$DesktopEntryPath" << EOF
[Desktop Entry]
Type=Application
Name=$AppName
Comment=$Comment
Icon=$IconPath
Exec=$ExecPath
Terminal=false
Categories=Utility;Application;
EOF

echo "Link $DesktopEntryPath to $LinkPath"
ln -s $DesktopEntryPath $LinkPath

echo "*************CreateDsektop Finsih*************"