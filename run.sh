#!/bin/bash

IMAGE_NAME="roam-semantic-search"
PORT="8000"

# Check if container with this image is already running
EXISTING_CONTAINER=$(docker ps --filter "ancestor=$IMAGE_NAME" --format "{{.ID}}")

if [ -n "$EXISTING_CONTAINER" ]; then
  echo "✅ Container already running at http://localhost:$PORT"
  docker ps --filter "ancestor=$IMAGE_NAME"
  exit 0
fi

# If port is in use (by some zombie container), stop and remove it
USED_CONTAINER=$(docker ps --filter "publish=$PORT" --format "{{.ID}}")

if [ -n "$USED_CONTAINER" ]; then
  echo "🛑 Stopping container using port $PORT..."
  docker stop "$USED_CONTAINER"
  docker rm "$USED_CONTAINER"
fi

echo "🔨 Building image..."
docker build -t $IMAGE_NAME .

echo "🚀 Starting container on port $PORT..."
docker run -d -p $PORT:$PORT $IMAGE_NAME

echo "🌐 Ready at http://localhost:$PORT"