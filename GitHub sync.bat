@echo off
chcp 65001 >nul
echo ========================================
echo   正在自动打包并同步代码至 GitHub...
echo ========================================
echo.

:: 强制进入您的项目目录
cd /d D:\Flight-Tracker

:: Git 自动化三部曲
git add .
git commit -m "Auto-sync: %date% %time%"
git push

echo.
echo ========================================
echo   同步圆满完成！代码已安全存入云端。
echo ========================================
timeout /t 3