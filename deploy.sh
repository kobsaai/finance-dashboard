#!/bin/bash
set -e

REPO_DIR="/home/ubuntu/finance-dashboard"
STREAMLIT_APP_FILE="main.py"
VENV_DIR="$REPO_DIR/streamlit_venv"
LOGFILE="$REPO_DIR/streamlit.log"

echo "[$(date)] Pulling latest changes..." >> $LOGFILE
cd $REPO_DIR
git pull origin main >> $LOGFILE 2>&1

# Virtuelle Umgebung erstellen, falls nicht vorhanden
if [ ! -d "$VENV_DIR" ]; then
    echo "[$(date)] Creating virtual environment..." >> $LOGFILE
    python3 -m venv $VENV_DIR
fi

# Abhängigkeiten installieren
source $VENV_DIR/bin/activate
echo "[$(date)] Installing dependencies..." >> $LOGFILE
pip install --upgrade pip >> $LOGFILE 2>&1
if [ -f requirements.txt ]; then
    pip install -r requirements.txt >> $LOGFILE 2>&1
fi

# Vorherige tmux-Session beenden, falls sie existiert
if tmux has-session -t streamlit_app 2>/dev/null; then
    tmux kill-session -t streamlit_app
fi

# Neue tmux-Session starten
echo "[$(date)] Starting Streamlit in tmux..." >> $LOGFILE
tmux new-session -d -s streamlit_app "cd $REPO_DIR && source $VENV_DIR/bin/activate && streamlit run $STREAMLIT_APP_FILE >> $LOGFILE 2>&1"
