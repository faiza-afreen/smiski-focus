@echo off
cd /d "%~dp0"

echo Installing Smiski Focus dependencies...
py -3.11 -m pip install -r requirements.txt

if errorlevel 1 (
    echo Installation failed. Make sure Python 3.11 is installed.
    pause
    exit /b 1
)

echo Installation complete!
pause