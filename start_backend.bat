@echo off
chcp 65001 >nul
echo ======================================
echo    JobMatch AI - FastAPI Backend
echo ======================================
echo.
cd /d "%~dp0backend"

echo [1/2] 清理已有进程和端口 8000 ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do (
    echo   关闭进程 PID=%%a
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/2] 启动 FastAPI 服务 ...
echo.
echo    访问地址: http://localhost:8000
echo    按 Ctrl+C 停止服务
echo.
C:\Users\廖容\.workbuddy\binaries\python\versions\3.14.3\python.exe -W ignore::DeprecationWarning run.py
pause
