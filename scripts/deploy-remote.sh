#!/bin/bash

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Connected to VPS - Starting Deploy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd /root/roam-semantic-search

echo "📦 Pulling latest from GitHub..."
git fetch origin
git reset --hard origin/main

echo "🔐 Making scripts executable..."
chmod +x start.sh stop.sh restart.sh

echo "🔨 Rebuilding and restarting containers..."
./restart.sh rebuild

echo "⏳ Waiting for API to boot..."
attempts=0
until curl -s -f http://localhost:8000/ > /dev/null; do
  ((attempts++))
  if [ $attempts -ge 10 ]; then
    echo "❌ API not responding after 10 attempts"
    echo "Logs from container:"
    ./start.sh logs
    exit 1
  fi
  sleep 1
  echo "...retrying ($attempts)"
done

echo "✅ API is running at root route"
echo "🎉 EVERYTHING IS OKAY"

# Show recent logs
echo "📝 Recent logs:"
./start.sh logs --tail 20
