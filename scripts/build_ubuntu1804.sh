#!/bin/bash -e

pyinstaller main.py
mkdir deploy
tar -zcvf deploy/TkInterTest-Ubuntu1804.tar.gz -C dist
