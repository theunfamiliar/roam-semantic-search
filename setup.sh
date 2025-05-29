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

# Check if Docker is running and try to start it if not
if ! docker info &> /dev/null; then
    echo "⚠️ Docker is installed but not running"
    echo "🔄 Attempting to start Docker..."
    
    # Try to start Docker based on the OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - try to start Docker Desktop
        open -a Docker
        echo "⏳ Waiting for Docker to start..."
        for i in {1..30}; do
            if docker info &> /dev/null; then
                echo "✅ Docker started successfully"
                break
            fi
            sleep 1
            echo -n "."
            if [ $i -eq 30 ]; then
                echo
                echo "❌ Timeout waiting for Docker to start"
                echo "Please start Docker Desktop manually"
                exit 1
            fi
        done
    else
        # Linux - try to start Docker daemon
        if command -v systemctl &> /dev/null; then
            echo "🔄 Starting Docker daemon..."
            sudo systemctl start docker
            if ! docker info &> /dev/null; then
                echo "❌ Failed to start Docker daemon"
                echo "Please run: sudo systemctl start docker"
                exit 1
            fi
            echo "✅ Docker daemon started successfully"
        else
            echo "❌ Could not start Docker automatically"
            echo "Please start Docker manually:"
            echo "  sudo systemctl start docker    # on Linux"
            echo "  open -a Docker                 # on macOS"
            exit 1
        fi
    fi
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
echo "Run it with: ./start.sh" 