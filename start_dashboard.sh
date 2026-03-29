#!/bin/bash

echo -ne "\033]0;Launching DoppelBot Dashboard...\007"

echo "Checking for missing requirements..."
python3 -c "import flask, requests, discord" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "First launch or missing modules detected - this may take around 15-25 minutes!"
    python3 -m pip install -r requirements.txt
    python3 -m pip install flask requests
fi

clear
echo "==================================================="
echo "             DOPPELBOT DASHBOARD SETUP"
echo "==================================================="
echo ""
echo "Please select which dashboard you want to launch:"
echo ""
echo "[1] Desktop Application (Recommended)"
echo "[2] Web Dashboard (Browser Alternative)"
echo "[3] Start Bot Directly + Desktop Dashboard in Background"
echo ""
read -p "Enter 1, 2, or 3: " choice

if [ "$choice" == "3" ]; then
    echo ""
    echo "Starting Bot and Desktop Dashboard..."
    python3 launcher.py &
    python3 -c "import dotenv" 2>/dev/null || python3 -m pip install -q -r requirements.txt && python3 bot.py
elif [ "$choice" == "2" ]; then
    echo ""
    echo "Starting Web Dashboard..."
    echo "Please leave this window open. The dashboard will open in your browser shortly."
    open "http://127.0.0.1:5000/?reload=$RANDOM"
    python3 web_launcher.py
else
    echo ""
    echo "Starting Desktop Dashboard..."
    python3 launcher.py &
fi
exit 0