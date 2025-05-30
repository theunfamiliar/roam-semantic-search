#!/bin/bash

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Connected to VPS - Starting Deploy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd /root/roam-semantic-search

# Store the current git hash and file hashes
OLD_GIT_HASH=$(git rev-parse HEAD)
OLD_REQ_HASH=$(md5sum requirements.txt 2>/dev/null || echo "none")
OLD_DOCKER_HASH=$(md5sum Dockerfile 2>/dev/null || echo "none")
OLD_COMPOSE_HASH=$(md5sum docker-compose.yml docker-compose.*.yml 2>/dev/null | sort | md5sum || echo "none")

echo "📦 Pulling latest from GitHub..."
git fetch origin
git reset --hard origin/main

# Get new hashes
NEW_GIT_HASH=$(git rev-parse HEAD)
NEW_REQ_HASH=$(md5sum requirements.txt 2>/dev/null || echo "none")
NEW_DOCKER_HASH=$(md5sum Dockerfile 2>/dev/null || echo "none")
NEW_COMPOSE_HASH=$(md5sum docker-compose.yml docker-compose.*.yml 2>/dev/null | sort | md5sum || echo "none")

echo "🔐 Making scripts executable..."
chmod +x start.sh stop.sh restart.sh setup.sh

# Check if Docker is running
echo "🔍 Checking Docker status..."
if ! docker info &> /dev/null; then
    echo "⚠️ Docker is not running or not installed"
    echo "🔧 Running setup script..."
    ./setup.sh
    
    # Check again after setup
    if ! docker info &> /dev/null; then
        echo "❌ Docker setup failed. Please check the server manually."
        exit 1
    fi
    echo "✅ Docker is now running"
fi

# Determine if we need to rebuild
NEED_REBUILD=0
if [ "$OLD_REQ_HASH" != "$NEW_REQ_HASH" ]; then
    echo "📦 Requirements.txt changed - rebuild needed"
    NEED_REBUILD=1
fi

if [ "$OLD_DOCKER_HASH" != "$NEW_DOCKER_HASH" ]; then
    echo "🐳 Dockerfile changed - rebuild needed"
    NEED_REBUILD=1
fi

if [ "$OLD_COMPOSE_HASH" != "$NEW_COMPOSE_HASH" ]; then
    echo "🔄 Docker Compose configuration changed - rebuild needed"
    NEED_REBUILD=1
fi

# Check if any Python files changed
if git diff --name-only $OLD_GIT_HASH $NEW_GIT_HASH | grep -q "\.py$"; then
    echo "🐍 Python files changed - rebuild needed"
    NEED_REBUILD=1
fi

if [ $NEED_REBUILD -eq 1 ]; then
    echo "🔨 Changes detected - Rebuilding containers..."
    ./restart.sh rebuild
else
    echo "✨ No significant changes detected - Restarting without rebuild..."
    ./restart.sh
fi

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
