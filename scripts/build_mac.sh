#!/bin/bash -e

/Users/travis/Library/Python/3.7/bin/pyinstaller --onefile main.py
mkdir deploy
tar -zcvf deploy/TkInterTest-Mac.tar.gz -C dist main
