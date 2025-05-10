#!/bin/bash

# Kill any process using port 8001
echo "🧨 Checking for processes on port 8001..."
PID=$(lsof -ti:8001)
if [ ! -z "$PID" ]; then
  echo "🔪 Killing process $PID using port 8001..."
  kill -9 $PID
else
  echo "✅ Port 8001 is free."
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
  echo "🐍 Activating virtual environment..."
  source .venv/bin/activate
else
  echo "⚠️  No virtual environment found. Running with system Python."
fi

# Start Uvicorn server on port 8001
echo "🚀 Starting Uvicorn on http://127.0.0.1:8001 ..."
uvicorn server:app --reload --port 8001