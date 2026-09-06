#!/bin/bash
# Azure VM Deployment & Verification Script for Blinkit Stock Tracker

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$REPO_DIR" || exit 1

echo "=================================================="
echo "      AZURE VM BLINKIT BOT SETUP & STARTUP        "
echo "=================================================="

# 1. Pull latest code from GitHub
echo "[1/4] Pulling latest code from GitHub..."
git pull origin main

# 2. Check Python environment
if [ -f "$REPO_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$REPO_DIR/venv/bin/python"
elif [ -f "$REPO_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$REPO_DIR/.venv/bin/python"
else
    PYTHON_BIN=$(which python3)
fi

echo "[+] Using Python Binary: $PYTHON_BIN"

# 3. Ensure required dependencies installed
echo "[2/4] Verifying dependencies..."
$PYTHON_BIN -m pip install -q -r requirements.txt

# 4. Configure Task 1: 30-Minute Cron Job (main.py)
echo "[3/4] Setting up Task 1: 30-Minute Cron Job (main.py)..."
touch "$REPO_DIR/tracker.log"
CRON_JOB="*/30 * * * * cd $REPO_DIR && $PYTHON_BIN main.py >> $REPO_DIR/tracker.log 2>&1"
# Purge all old crons (main.py, discord_bot, channel_listener, webhook_server) and set fresh cron
(crontab -l 2>/dev/null | grep -v -E "main.py|discord_bot|discord_channel|webhook_server"; echo "$CRON_JOB") | crontab -

# 5. Configure Task 2: Background Discord Listener Bot (discord_bot.py)
echo "[4/4] Setting up Task 2: Background Discord Bot Listener (discord_bot.py)..."
touch "$REPO_DIR/bot.log"

if [ -f "$REPO_DIR/.env" ]; then
    echo "[+] Loading environment variables from .env..."
    set -a
    source "$REPO_DIR/.env"
    set +a
fi

# Kill all previous bot/listener instances
pkill -9 -f "discord_bot.py" 2>/dev/null
pkill -9 -f "discord_channel_listener.py" 2>/dev/null
pkill -9 -f "webhook_server.py" 2>/dev/null
sleep 1
nohup $PYTHON_BIN "$REPO_DIR/discord_bot.py" >> "$REPO_DIR/bot.log" 2>&1 &

sleep 2

echo "\n=================================================="
echo "      VERIFICATION & RUNTIME STATUS SUMMARY       "
echo "=================================================="
echo "1. Crontab (Task 1 - Every 30 mins):"
crontab -l | grep "main.py"

echo "\n2. Discord Bot Listener Process (Task 2):"
ps aux | grep "discord_bot.py" | grep -v "grep"

echo "\n3. Bot Listener Log Output:"
tail -n 10 "$REPO_DIR/bot.log"

echo "--------------------------------------------------"
echo "Setup Complete! Both tasks are live and running on your Azure VM."

