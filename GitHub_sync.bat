@echo off
echo ========================================
echo  [Debug Mode] Syncing codebase to GitHub
echo ========================================
echo.

REM 1. Force directory change to absolute path
cd /d D:\Flight-Tracker

REM 2. Print current Git status
echo [*] Checking current Git status:
git status
echo.

REM 3. Execute sync pipeline
echo [*] Staging changes...
git add .

echo [*] Generating version snapshot...
git commit -m "Auto-sync: %date% %time%"

echo [*] Pushing to cloud repository...
git push

echo.
echo ========================================
echo  Pipeline executed. Check for errors above.
echo ========================================
REM Pause to keep the terminal window open
pause