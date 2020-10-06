#!/bin/bash -e

pyinstaller main.py
mkdir deploy
/C/Program\ Files/7-zip/7z.exe a deploy/TkInterTest-Win.zip ./dist/*
