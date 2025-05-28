#!/bin/bash

set -e

print() {
  echo -e "\033[1;36m$1\033[0m"
}

COMMIT_MSG="${1:-.}"

print "🔧 Committing local changes..."
git add .
git commit -m "$COMMIT_MSG" || echo "⚠️ Nothing to commit."
git push origin main

print "🌐 SSHing into VPS to deploy..."
DEPLOY_OUTPUT=$(ssh -tt singularity bash << 'EOF'
  set -e
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📍 Connected to VPS - Starting Deploy"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  cd /root/roam-semantic-search
  chmod +x ./scripts/*.sh

  echo "📦 Pulling latest from GitHub..."
  git fetch origin
  git reset --hard origin/main

  echo "🧠 Checking for server.py..."
  [ -f server.py ] || { echo "❌ server.py not found"; exit 1; }

  echo "🛑 Stopping API service..."
  systemctl stop semantic-api.service
  pkill -f uvicorn || true
  sleep 2

  echo "🔄 Checking port 8000..."
  if lsof -i :8000 > /dev/null; then
    echo "❌ Port 8000 in use"; exit 1
  else
    echo "✅ Port 8000 is free"
  fi

  echo "🔁 Restarting API service..."
  systemctl start semantic-api.service
  sleep 3

  echo "🧾 Checking root route..."
  attempts=0
  until curl -s -f http://localhost:8000/ > /dev/null; do
    ((attempts++))
    if [ $attempts -ge 10 ]; then
      echo "❌ API not responding at root route after 10 attempts"
      exit 1
    fi
    sleep 1
    echo "...retrying ($attempts)"
  done

  echo "✅ DEPLOY SUCCESSFUL"
EOF
)

echo "$DEPLOY_OUTPUT"

if echo "$DEPLOY_OUTPUT" | grep -q "✅ DEPLOY SUCCESSFUL"; then
  echo -e "\n🎉 DEPLOY CONFIRMED: Everything is okay."
else
  echo -e "\n❌ Deploy may have failed. Check logs above."
fi