#!/bin/bash

set -e

# 📝 Optional commit message
COMMIT_MSG="${1:-.}"

# 📜 Log to timestamped file
mkdir -p logs
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
logfile="logs/deploy-$timestamp.log"
exec > >(tee -a "$logfile") 2>&1

# 🚀 Local Git push
echo "▶️ Committing changes to GitHub..."
git add .
git commit -m "$COMMIT_MSG" || echo "⚠️ Nothing to commit."
git push --force origin main

# 📡 SSH into VPS and deploy
echo "🚀 SSHing into VPS and pulling latest code..."
ssh -tt singularity << 'ENDSSH'
  set -e

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📍 Connected to VPS - Starting Deploy"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  cd /root/roam-semantic-search

  echo "🔐 Making scripts executable..."
  chmod +x ./scripts/*.sh

  echo "📦 Pulling latest from GitHub..."
  git fetch origin
  git reset --hard origin/main

  echo "🧠 Checking for server.py..."
  if [ ! -f server.py ]; then
    echo "❌ server.py not found"; exit 1
  fi

  echo "🛑 Stopping API service..."
  systemctl stop semantic-api.service
  pkill -f uvicorn || true
  sleep 2

  echo "🔄 Checking port 8000..."
  if lsof -i :8000; then
    echo "❌ Port 8000 in use"; exit 1
  else
    echo "✅ Port 8000 is free"
  fi

  echo "🔁 Restarting API service..."
  systemctl start semantic-api.service

  echo "🧾 Checking root route..."
  sleep 3
  ROOT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
  if [ "$ROOT_STATUS" == "200" ]; then
    echo "✅ API is running at root route."
    echo "🎉 Deployment successful!"
  else
    echo "❌ Root route failed with status $ROOT_STATUS"; exit 1
  fi
ENDSSH