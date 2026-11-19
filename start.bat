@echo off
cd /d "%~dp0"

py -3.11 launcher.pyw

if errorlevel 1 pause