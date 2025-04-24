#!/bin/bash
set -e

REPO_DIR="finance-dashboard"
STREAMLIT_APP_FILE="main.py"  # Anpassen an deinen Dateinamen

echo "Pulling latest changes from GitHub..."
cd $REPO_DIR
git pull origin main  # oder master

echo "Installing/updating dependencies..."
pip install -r requirements.txt

echo "Restarting Streamlit app..."
# Kill any existing Streamlit process
pkill -f streamlit || true

# Start Streamlit in a new tmux session
tmux new-session -d -s streamlit_app "cd $REPO_DIR && streamlit run $STREAMLIT_APP_FILE"

echo "Deployment completed successfully!"