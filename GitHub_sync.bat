@echo off
chcp 65001 >nul
echo ========================================
echo   [Debug 模式] 正在同步代码至 GitHub...
echo ========================================
echo.

:: 1. 强制进入项目绝对路径
cd /d D:\Flight-Tracker

:: 2. 打印当前 Git 状态
echo [*] 当前 Git 状态检查：
git status
echo.

:: 3. 执行同步管线
echo [*] 正在暂存变更...
git add .

echo [*] 正在生成版本快照...
git commit -m "Auto-sync: %date% %time%"

echo [*] 正在推送至云端...
git push

echo.
echo ========================================
echo   执行管线结束。请检查上方是否有 error 提示。
echo ========================================
:: 强制暂停，等待用户手动关闭窗口，防止报错信息一闪而过
pause