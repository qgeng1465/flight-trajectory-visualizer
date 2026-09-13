@echo off
chcp 65001 >nul
title Flight Tracker - Local Server
cd /d "%~dp0"

echo ========================================
echo   Flight Footprints - Local Server
echo ========================================
echo.

start "" /B cmd /c "ping 127.0.0.1 -n 3 >nul & start """" "http://localhost:8000""

echo [*] Serving http://localhost:8000   (this machine only)
echo [*] Keep this window open. Press Ctrl+C to stop.
echo.

rem Try the launcher first, fall back to plain python.
py -3 -m http.server 8000 --bind 127.0.0.1 2>nul || python -m http.server 8000 --bind 127.0.0.1
pause
