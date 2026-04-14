@echo off
title Flight Tracker Local Server

echo ========================================
echo  Initializing Local Visualization Engine
echo ========================================
echo.

REM 1. Force absolute path execution
cd /d D:\Flight-Tracker

REM 2. Asynchronous browser launch with 2-second delay to prevent TCP SYN rejection
REM Using ping as a high-precision cross-compatible sleep command
start "" /B cmd /c "ping 127.0.0.1 -n 3 >nul & start """" "http://localhost:8000""

REM 3. Bind high-performance Python HTTP daemon to port 8000 (Blocking Process)
echo [*] Server daemon is binding to 0.0.0.0:8000
echo [*] DO NOT close this terminal window.
echo [*] Press Ctrl+C to terminate the service safely.
echo.
python -m http.server 8000