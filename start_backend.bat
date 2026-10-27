@echo off
echo ╔══════════════════════════════════════╗
echo ║   DarkAI — Backend Startup           ║
echo ╚══════════════════════════════════════╝

cd /d "%~dp0backend"

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Installing dependencies...
venv\Scripts\pip.exe install -r requirements.txt -q

echo.
echo Starting DarkAI FastAPI server...
echo API Docs: http://localhost:8000/api/docs
echo.

venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
