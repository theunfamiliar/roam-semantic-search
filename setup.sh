#!/bin/bash

echo "🔍 Checking prerequisites..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    echo
    echo "Quick install commands:"
    echo "Mac (with homebrew):"
    echo "  brew install --cask docker"
    echo
    echo "Ubuntu/Debian:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is installed but not running"
    echo "Please start Docker Desktop or run:"
    echo "  sudo systemctl start docker    # on Linux"
    exit 1
fi

# Check for docker compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    echo "It should be included with Docker Desktop"
    echo "If you're on Linux, you might need to install it separately:"
    echo "  sudo apt-get install docker-compose-plugin"
    exit 1
fi

echo "✅ Docker is installed and running"
echo "✅ Docker Compose is available"
echo
echo "🎉 You're ready to run the application!"
echo "Run it with: ./run.sh" 