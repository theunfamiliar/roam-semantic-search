#!/bin/bash

set -e

# ─────────────────────────────────────────────────────────────
# 📝 Accept optional commit message
# ─────────────────────────────────────────────────────────────
COMMIT_MSG="${1:-.}"

# ─────────────────────────────────────────────────────────────
# 📜 Logging Setup
# ─────────────────────────────────────────────────────────────
mkdir -p logs
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
logfile="logs/deploy-$timestamp.log"
exec > >(tee -a "$logfile") 2>&1

# ─────────────────────────────────────────────────────────────
# 🚀 Local Git Commit + Push
# ─────────────────────────────────────────────────────────────
echo "▶️ Committing changes to GitHub..."
git add .
git commit -m "$COMMIT_MSG" || echo "⚠️ Nothing to commit."
git push --force origin main

# ─────────────────────────────────────────────────────────────
# 📡 SSH into VPS and deploy
# ─────────────────────────────────────────────────────────────
echo "🚀 SSHing into VPS and pulling latest code..."
ssh singularity << 'ENDSSH'
  set -e

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📍 Connected to VPS - Starting Deploy"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  cd /root/roam-semantic-search

  echo "📦 Forcing latest from GitHub (reset)..."
  git fetch origin
  git reset --hard origin/main

  echo "🧠 Checking for server.py..."
  if [ ! -f server.py ]; then
    echo "❌ server.py not found"; exit 1
  fi

  echo "🛑 Releasing port 8000 if blocked..."
  fuser -k 8000/tcp || true

  echo "🔄 Restarting API service..."
  systemctl restart semantic-api.service

  echo "🪵 Dumping last 30 log lines from semantic-api.service..."
  journalctl -u semantic-api.service -n 30 --no-pager

  echo "⏳ Waiting for API to boot..."
  sleep 3

  echo "📡 Hitting root route..."
  ROOT_OUTPUT=$(curl -s -w "\\nHTTP_STATUS:%{http_code}" http://localhost:8001/)
  ROOT_STATUS=$(echo "$ROOT_OUTPUT" | tail -n1 | sed 's/HTTP_STATUS://')
  ROOT_BODY=$(echo "$ROOT_OUTPUT" | sed '$d')
  echo "🌐 Status: $ROOT_STATUS"
  echo "📝 Body: $ROOT_BODY"
  if [ "$ROOT_STATUS" != "200" ]; then
    echo "❌ Root route failed"; exit 1
  fi

  echo "📡 Hitting /search route..."
  SEARCH_OUTPUT=$(curl -s -w "\\nHTTP_STATUS:%{http_code}" -u admin:secret -H "Content-Type: application/json" \
    -d '{"query":"test","top_k":1}' http://localhost:8001/search)
  SEARCH_STATUS=$(echo "$SEARCH_OUTPUT" | tail -n1 | sed 's/HTTP_STATUS://')
  SEARCH_BODY=$(echo "$SEARCH_OUTPUT" | sed '$d')
  echo "🌐 Status: $SEARCH_STATUS"
  echo "📝 Body: $SEARCH_BODY"

  if [ "$SEARCH_STATUS" != "200" ]; then
    echo "⚠️ Search route failed, attempting reindex..."

    echo "🔁 Reindexing..."
    REINDEX_OUTPUT=$(curl -s -w "\\nHTTP_STATUS:%{http_code}" -u admin:secret -X POST http://localhost:8001/reindex)
    REINDEX_STATUS=$(echo "$REINDEX_OUTPUT" | tail -n1 | sed 's/HTTP_STATUS://')
    REINDEX_BODY=$(echo "$REINDEX_OUTPUT" | sed '$d')
    echo "🌐 Status: $REINDEX_STATUS"
    echo "📝 Body: $REINDEX_BODY"
    if [ "$REINDEX_STATUS" != "200" ]; then
      echo "❌ Reindex failed"; exit 1
    fi

    echo "✅ Reindex complete. Semantic API is now ready."
  else
    echo "✅ Search route responded successfully."
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "✅ Deploy Complete"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ENDSSH