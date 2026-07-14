@echo off
chcp 65001 >nul
setlocal
title GitHub Sync - Flight Footprints

REM Run from THIS folder, no matter where the .bat is double-clicked
cd /d "%~dp0"

echo =====================================================
echo   Flight Footprints  -  One-click GitHub Sync
echo =====================================================
echo.

REM 0. Sanity check: is this a git repository?
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This folder is not a git repository.
    echo         Put this file inside D:\Flight-Tracker and run again.
    goto :fail
)

REM 1. Stage everything (new / modified / deleted files)
echo [*] Staging all changes...
git add -A
if errorlevel 1 ( echo [ERROR] "git add" failed. & goto :fail )

REM 2. Commit only when something is actually staged
git diff --cached --quiet
if errorlevel 1 (
    echo [*] Creating commit...
    git commit -m "Auto-sync: %date% %time%"
    if errorlevel 1 ( echo [ERROR] "git commit" failed. & goto :fail )
) else (
    echo [i] No new local changes - will still pull/push to stay in sync.
)

REM 3. Pull latest (rebase) so the push is never rejected as non-fast-forward
echo [*] Pulling latest from GitHub...
git pull --rebase --autostash origin main
if errorlevel 1 (
    echo [ERROR] Pull failed. Check your network, or resolve conflicts then retry.
    goto :fail
)

REM 4. Push to GitHub
echo [*] Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo [ERROR] Push failed. Check network / GitHub login credentials.
    goto :fail
)

echo.
echo =====================================================
echo   [OK] Synced to GitHub successfully!
echo =====================================================
echo.
pause
exit /b 0

:fail
echo.
echo =====================================================
echo   [FAILED] Sync did not complete. See messages above.
echo =====================================================
echo.
pause
exit /b 1
