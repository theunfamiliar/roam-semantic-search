#!/bin/bash

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Connected to VPS - Starting Deploy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd /root/roam-semantic-search

# Store the current dependency-related file hashes
OLD_REQ_HASH=$(md5sum requirements.txt 2>/dev/null || echo "none")
OLD_DOCKER_HASH=$(md5sum Dockerfile 2>/dev/null || echo "none")
OLD_COMPOSE_HASH=$(md5sum docker-compose.yml 2>/dev/null || echo "none")

echo "📦 Pulling latest from GitHub..."
git fetch origin
git reset --hard origin/main

# Get new hashes
NEW_REQ_HASH=$(md5sum requirements.txt 2>/dev/null || echo "none")
NEW_DOCKER_HASH=$(md5sum Dockerfile 2>/dev/null || echo "none")
NEW_COMPOSE_HASH=$(md5sum docker-compose.yml 2>/dev/null || echo "none")

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

# Determine if we need to rebuild based on dependency changes
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

# Only rebuild if dependencies or configuration changed
if [ $NEED_REBUILD -eq 1 ]; then
    echo "🔨 Dependencies or configuration changed - Rebuilding containers..."
    docker compose build --no-cache app
    docker compose down
    docker compose up -d
else
    echo "✨ No dependency changes detected - Restarting with existing image..."
    # Stop containers but keep volumes
    docker compose down
    # Start containers with new code (using volumes)
    docker compose up -d
fi

echo "⏳ Waiting for API to boot..."
attempts=0
until curl -s -f http://localhost:8000/ > /dev/null; do
  ((attempts++))
  if [ $attempts -ge 10 ]; then
    echo "❌ API not responding after 10 attempts"
    echo "Logs from container:"
    docker compose logs app
    exit 1
  fi
  sleep 1
  echo "...retrying ($attempts)"
done

echo "✅ API is running at root route"
echo "🎉 EVERYTHING IS OKAY"

# Show recent logs
echo "📝 Recent logs:"
docker compose logs --tail 20 app
