@echo off
title Veritas-X Security Interceptor
echo [SYSTEM] Initializing Veritas-X AI...

:: Check if virtual environment exists and activate it
if exist venv\Scripts\activate (
    echo [SYSTEM] Activating Virtual Environment...
    call venv\Scripts\activate
)

echo [SYSTEM] Launching Interceptor...
python main.py

echo [SYSTEM] Session Ended.
pause