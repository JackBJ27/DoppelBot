#!/bin/bash

# Sets the terminal window title
echo -ne "\033]0;Launching DoppelBot Dashboard...\007"

echo "Checking for missing requirements..."
python3 -c "import flask, requests" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "First launch detected - this may take around 15-25 minutes!"
    python3 -m pip install -r requirements.txt
    python3 -m pip install flask requests
else
    python3 -m pip install -q -r requirements.txt
    python3 -m pip install -q flask requests
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
echo ""
read -p "Enter 1 or 2: " choice

if [ "$choice" == "2" ]; then
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