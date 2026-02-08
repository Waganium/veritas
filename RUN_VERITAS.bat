@echo off
title Veritas-X Apex: System Initialization
color 0b

echo =========================================================
echo        VERITAS-X APEX // BIOMETRIC INTERCEPTOR
echo =========================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [!] ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10 or higher.
    pause
    exit
)

echo [+] Checking Forensic Dependencies...
:: Installing specific versions for stability with the Apex engine
pip install opencv-python mediapipe mss pygetwindow numpy scipy --quiet

if %errorlevel% neq 0 (
    echo [!] Dependency installation failed. Checking internet connection...
    pause
    exit
)

echo [+] Dependencies Verified.
echo [+] Launching Veritas-X Controller...
echo.

:: Change "MAIN.PY" to whatever your filename is
python MAIN.PY

echo.
echo =========================================================
echo        SYSTEM TERMINATED // SESSIONS CLOSED
echo =========================================================
pause