@echo off
setlocal
title Veritas-X Apex: VENV Managed Environment
color 0b

:: --- CONFIGURATION ---
set "VENV_DIR=vx_env"
set "PYTHON_FILE=main.py"

echo =========================================================
echo        VERITAS-X APEX // VIRTUAL ENVIRONMENT
echo =========================================================
echo.

:: 1. Check if Python is even installed on the system
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [!] CRITICAL ERROR: Python not found in System PATH.
    echo Please install Python 3.10+ and check "Add to PATH".
    pause
    exit
)

:: 2. Create Virtual Environment if it doesn't exist
if not exist "%VENV_DIR%\" (
    echo [+] Creating isolated virtual environment: %VENV_DIR%...
    python -m venv %VENV_DIR%
)

:: 3. Activate the Environment
echo [+] Activating Veritas Environment...
call "%VENV_DIR%\Scripts\activate.bat"

:: 4. Install/Update Dependencies inside the VENV
echo [+] Syncing Forensic Libraries (OpenCV, MediaPipe, SciPy)...
python -m pip install --upgrade pip --quiet
python -m pip install opencv-python mediapipe mss pygetwindow numpy scipy --quiet

:: 5. Launch the Interceptor
echo [+] Environment Ready. Launching Interceptor...
echo.
python "%PYTHON_FILE%"

:: 6. Cleanup on Close
echo.
echo [+] Shutting down environment...
deactivate
echo =========================================================
echo        SYSTEM STANDBY
echo =========================================================
pause