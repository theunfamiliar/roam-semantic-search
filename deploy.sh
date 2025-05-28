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

# DO NOT use here-document — pass a script directly over SSH with -tt
ssh -tt singularity bash -s <<'EOF'
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

echo "⏳ Waiting for API to boot..."
sleep 3

echo "🧾 Checking root route..."
attempts=0
until curl -s -f http://localhost:8000/ > /dev/null; do
  ((attempts++))
  if [ $attempts -ge 10 ]; then
    echo "❌ API not responding at root route after 10 attempts"; exit 1
  fi
  sleep 1
  echo "...retrying ($attempts)"
done

echo "✅ API is running at root route."
echo "🎉 EVERYTHING IS OKAY"
EOF