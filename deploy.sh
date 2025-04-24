#!/bin/bash
set -e

REPO_DIR="finance-dashboard"  # Passe diesen Pfad an
STREAMLIT_APP_FILE="main.py"  # Anpassen an deinen Dateinamen
VENV_DIR="$REPO_DIR/streamlit_venv"

echo "Pulling latest changes from GitHub..."
cd $REPO_DIR
git pull origin main

# Virtuelle Umgebung erstellen, falls nicht vorhanden
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# Aktiviere virtuelle Umgebung
source $VENV_DIR/bin/activate

echo "Installing/updating dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

echo "Restarting Streamlit app..."
# Kill any existing Streamlit process
pkill -f streamlit || true

# Start Streamlit in a new tmux session
tmux new-session -d -s streamlit_app "cd $REPO_DIR && source $VENV_DIR/bin/activate && streamlit run $STREAMLIT_APP_FILE"

echo "Deployment completed successfully!"