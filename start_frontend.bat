@echo off
echo ╔══════════════════════════════════════╗
echo ║   DarkAI — Frontend Startup          ║
echo ╚══════════════════════════════════════╝

set "PATH=C:\Users\DELL\OneDrive\Desktop\puturknowledge\node-v20.14.0-win-x64;%PATH%"

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Installing npm dependencies (first run)...
    npm install
)

echo.
echo Starting DarkAI Vite frontend...
echo App: http://localhost:5173
echo.

npm run dev
