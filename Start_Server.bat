@echo off
chcp 65001 >nul
title Flight Tracker Local Server

echo ========================================
echo   正在初始化本地飞行轨迹可视化引擎...
echo ========================================
echo.

:: 强制进入绝对路径
cd /d D:\Flight-Tracker

:: 唤醒系统默认浏览器并访问本地端口
echo [*] 正在唤起默认浏览器...
start http://localhost:8000

:: 启动 Python 高性能 HTTP 服务器
echo [*] 本地服务器已启动，请勿关闭此窗口。
echo [*] 如需停止服务，请直接关闭本黑框。
echo.
python -m http.server 8000