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

  echo "🔐 Ensuring all scripts are executable..."
  chmod +x ./scripts/*.sh

  echo "📦 Forcing latest from GitHub (reset)..."
  git fetch origin
  git reset --hard origin/main

  echo "🧠 Checking for server.py..."
  if [ ! -f server.py ]; then
    echo "❌ server.py not found"; exit 1
  fi

  echo "🛑 Stopping systemd service (semantic-api.service)..."
  systemctl stop semantic-api.service

  echo "🔪 Killing any lingering uvicorn processes..."
  pkill -f uvicorn || true
  sleep 2

  echo "🔄 Verifying port 8000 is free..."
  if lsof -i :8000; then
    echo "❌ Port 8000 still in use!"; exit 1
  else
    echo "✅ Port 8000 successfully cleared"
  fi

  echo "🔄 Restarting API service..."
  systemctl start semantic-api.service

  echo "🪵 Dumping last 30 log lines from semantic-api.service..."
  journalctl -u semantic-api.service -n 30 --no-pager

  echo "⏳ Waiting for API to boot..."
  sleep 3

  echo "📡 Hitting root route..."
  ROOT_OUTPUT=$(curl -s -w "\nHTTP_STATUS:%{http_code}" http://localhost:8000/)
  HTTP_STATUS=$(echo "$ROOT_OUTPUT" | grep HTTP_STATUS | cut -d':' -f2)
  ROOT_BODY=$(echo "$ROOT_OUTPUT" | sed '$d')
  echo "📝 Body: $ROOT_BODY"
  if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Root route responded OK"
  else
    echo "❌ Root route failed with status $HTTP_STATUS"
    exit 1
  fi

  echo "📡 Hitting /reindex route..."
  REINDEX_OUTPUT=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -u admin:secret -X POST http://localhost:8000/reindex)
  REINDEX_STATUS=$(echo "$REINDEX_OUTPUT" | grep HTTP_STATUS | cut -d':' -f2)
  REINDEX_BODY=$(echo "$REINDEX_OUTPUT" | sed '$d')
  echo "📝 Body: $REINDEX_BODY"
  if [ "$REINDEX_STATUS" = "200" ]; then
    echo "✅ Reindex succeeded"
  else
    echo "❌ Reindex failed with status $REINDEX_STATUS"
    exit 1
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🎉 EVERYTHING IS OKAY. Server is live and reindex is successful."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ENDSSH