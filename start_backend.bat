@echo off
echo ======================================
echo    JobMatch AI - FastAPI Backend
echo ======================================
echo.
cd /d "%~dp0backend"
echo Starting FastAPI server on http://localhost:8000
echo.
C:\Users\廖容\.workbuddy\binaries\python\versions\3.14.3\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
