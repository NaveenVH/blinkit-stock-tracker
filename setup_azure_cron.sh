#!/bin/bash
# Setup Script for running Blinkit Stock Tracker every 15 minutes via Crontab on Azure Linux VM

# Get current directory absolute path
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Identify Python environment
if [ -f "$REPO_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$REPO_DIR/venv/bin/python"
elif [ -f "$REPO_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$REPO_DIR/.venv/bin/python"
else
    PYTHON_BIN=$(which python3)
fi

# Create crontab command string
CRON_JOB="*/15 * * * * cd $REPO_DIR && $PYTHON_BIN main.py >> $REPO_DIR/tracker.log 2>&1"

# Add to crontab without duplicate entries
(crontab -l 2>/dev/null | grep -v "main.py"; echo "$CRON_JOB") | crontab -

echo "[+] Successfully configured Crontab on Azure VM!"
echo "--------------------------------------------------"
echo "Schedule:  Every 15 minutes (*/15 * * * *)"
echo "Directory: $REPO_DIR"
echo "Python:    $PYTHON_BIN"
echo "Logs:      $REPO_DIR/tracker.log"
echo "--------------------------------------------------"
echo "To check live logs on your VM:  tail -f tracker.log"
echo "To view current active cron:     crontab -l"
