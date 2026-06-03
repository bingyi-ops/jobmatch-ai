@echo off
echo ====================================
echo    JobMatch AI - Start Frontend
echo ====================================
echo.

cd /d "%~dp0frontend"
echo Starting dev server on http://localhost:5173
echo.
npx vite --host 0.0.0.0 --port 5173
pause
