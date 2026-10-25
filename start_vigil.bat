@echo off
cd /d "$~dp0"

start "VIGIL server" cmd /k "venv\scripts\python.exe -m uvicorn server:app"
timeout /t 5 /nobreak >nul
start http://127.0.0.1:8000/dashboard
start "VIGIL Detector" cmd /k "venv\scripts\python.exe step3.py"