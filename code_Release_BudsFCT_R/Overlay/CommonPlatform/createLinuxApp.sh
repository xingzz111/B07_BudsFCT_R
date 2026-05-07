#!/bin/bash

sudo true

BasePath=$(cd "$(dirname "$0")";pwd)


echo "-------------------- CreateApp Start --------------------"


if [ -f $BasePath/src/spec/PRMTester_linux.spec ]; then
	cd $BasePath
	rm -rf dist
	rm -rf build
	rm -rf __pycache__
	python3 -m PyInstaller $BasePath/src/spec/PRMTester_linux.spec
fi

if [ -d $BasePath/dist ]; then
  cp -r -p -f $BasePath/src/prmLib $BasePath/dist/
  cp -r -p -f $BasePath/src/configure $BasePath/dist/
  cp -r -p -f $BasePath/src/profile $BasePath/dist/
  # cp -r -p -f $BasePath/src/seqcore $BasePath/dist/
  # cp -r -p -f $BasePath/src/engine $BasePath/dist/
  mkdir -p $BasePath/dist/img
  cp -r -p -f $BasePath/src/gui/img/icon.png $BasePath/dist/img/
  cp -r -p -f $BasePath/createDesktop.sh $BasePath/dist/
fi

if [ -f $BasePath/src/signer/prmsigner_linux ]; then
  echo "-------------------- Start signature project ----------------------"
	chmod 777 $BasePath/src/signer/prmsigner_linux
	$BasePath/src/signer/prmsigner_linux -d $BasePath/dist
	echo "-------------------- End signature project ----------------------"
else
	echo "!!!!!!!!!!!!!!!!!!!!!!!! Not signature tool !!!!!!!!!!!!!!!!!!!!!!!!"
	echo "!!!!!!!!!!!!!!!!!!!!!! Skip signature project !!!!!!!!!!!!!!!!!!!!!!"
fi

rm -rf build
mv dist PRMTester

echo "-------------------- CreateApp End ----------------------"

exit 0

