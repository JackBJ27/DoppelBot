@echo off
title Launching DoppelBot Dashboard...

echo Checking for missing requirements...
python -c "import flask, requests, discord" 2>nul

if errorlevel 1 (
    echo First launch or missing modules detected - this may take around 15-25 minutes!
    python -m pip install -r requirements.txt
    python -m pip install flask requests
)

cls
echo ===================================================
echo             DOPPELBOT DASHBOARD SETUP
echo ===================================================
echo.
echo Please select which dashboard you want to launch:
echo.
echo [1] Desktop Application (Recommended)
echo [2] Web Dashboard (Browser Alternative)
echo [3] Start Bot Directly + Desktop Dashboard in Background
echo.
set /p choice="Enter 1, 2, or 3: "

if "%choice%"=="3" (
    echo.
    echo Starting Bot and Desktop Dashboard...
    start "" pythonw launcher.py
    start "DoppelBot Terminal" cmd /k "python -c \"import dotenv\" 2>nul || python -m pip install -q -r requirements.txt & python bot.py"
    exit
) else if "%choice%"=="2" (
    echo.
    echo Starting Web Dashboard...
    echo Please leave this window open. The dashboard will open in your browser shortly.
    start "" "http://127.0.0.1:5000/?reload=%random%"
    python web_launcher.py
) else (
    echo.
    echo Starting Desktop Dashboard...
    start "" pythonw launcher.py
)
exit
