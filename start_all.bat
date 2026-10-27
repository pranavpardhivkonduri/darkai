@echo off
echo ╔══════════════════════════════════════╗
echo ║   DarkAI — Launch Full Application    ║
echo ╚══════════════════════════════════════╝
echo.
echo Starting Backend Server on http://localhost:8000 ...
start "DarkAI Backend" cmd /c "%~dp0start_backend.bat"

echo Starting Frontend Dev Server on http://localhost:5173 ...
start "DarkAI Frontend" cmd /c "%~dp0start_frontend.bat"

echo.
echo Both servers launching! 
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/api/docs
echo.
pause
