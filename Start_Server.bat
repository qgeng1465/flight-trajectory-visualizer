@echo off
chcp 65001 >nul
title Flight Tracker - Local Server
cd /d "%~dp0"

echo ========================================
echo  Initializing Local Visualization Engine
echo ========================================
echo.

start "" /B cmd /c "ping 127.0.0.1 -n 3 >nul & start """" "http://localhost:8000""

echo [*] Server is binding to 0.0.0.0:8000
echo [*] Keep this window open. Press Ctrl+C to stop.
echo.
python -m http.server 8000
