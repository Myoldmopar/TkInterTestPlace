#!/bin/bash -e

pyinstaller --onefile main.py
mkdir deploy
/C/Program\ Files/7-zip/7z.exe a deploy/TkInterTest-Win.zip ./dist/*
