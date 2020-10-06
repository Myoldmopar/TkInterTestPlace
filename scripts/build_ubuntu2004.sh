#!/bin/bash -e

pyinstaller main.py
mkdir deploy
tar -zcvf deploy/TkInterTest-Ubuntu2004.tar.gz -C dist main
