@echo off
title Launching DoppelBot Dashboard...

echo Checking for missing requirements...
:: Forcing the py -3.13 launcher to keep everything in the exact same environment
py -3.13 -c "import flask, requests, discord" 2>nul

if errorlevel 1 (
    echo First launch or missing modules detected - this may take around 15-25 minutes!
    py -3.13 -m pip install -r requirements.txt
    py -3.13 -m pip install flask requests
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
    start "" pyw -3.13 launcher.py
    :: Uses your exact cmd_chain logic with the inline dotenv check
    start "DoppelBot Terminal" cmd /k "py -3.13 -c \"import dotenv\" 2>nul || py -3.13 -m pip install -q -r requirements.txt & py -3.13 bot.py"
    exit
) else if "%choice%"=="2" (
    echo.
    echo Starting Web Dashboard...
    echo Please leave this window open. The dashboard will open in your browser shortly.
    start "" "http://127.0.0.1:5000/?reload=%random%"
    py -3.13 web_launcher.py
) else (
    echo.
    echo Starting Desktop Dashboard...
    start "" pyw -3.13 launcher.py
)
exit
