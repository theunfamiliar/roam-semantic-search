#!/bin/bash

# Create run logs directory if it doesn't exist
mkdir -p logs/run

# Set up application log directories
./scripts/setup_logs.sh

# Log file with timestamp
LOG_FILE="logs/run/run-$(date +%Y%m%d-%H%M%S).log"

# Function to log messages to both console and file
log() {
    echo "$@" | tee -a "$LOG_FILE"
}

# Check if Docker is available and running
if ! docker info &> /dev/null; then
    log "❌ Docker is not running or not installed"
    log "Please run: ./setup.sh"
    log "This will check your system and guide you through installation"
    exit 1
fi

# Default to development mode (showing logs)
MODE=${1:-dev}

log "Starting application in $MODE mode..."
log "Logging to: $LOG_FILE"

# Function to show control commands help
show_control_help() {
    echo
    log "🎮 Control Commands:"
    log "  ./stop.sh         - Stop the server"
    log "  ./restart.sh      - Restart the server (supports same modes as start)"
    echo
}

case $MODE in
  "dev")
    # Run in development mode with logs visible
    log "🚀 Starting in development mode..."
    log "Stopping any existing containers..."
    docker compose down | tee -a "$LOG_FILE"
    log "Starting containers..."
    docker compose up 2>&1 | tee -a "$LOG_FILE"
    ;;
  "prod")
    # Run in production mode (detached)
    log "🚀 Starting in production mode..."
    log "Stopping any existing containers..."
    docker compose down | tee -a "$LOG_FILE"
    log "Starting containers in detached mode..."
    docker compose up -d 2>&1 | tee -a "$LOG_FILE"
    show_control_help
    ;;
  "logs")
    # Show logs
    docker compose logs -f 2>&1 | tee -a "$LOG_FILE"
    ;;
  "rebuild")
    # Rebuild and restart
    log "🔨 Rebuilding and restarting..."
    log "Stopping any existing containers..."
    docker compose down | tee -a "$LOG_FILE"
    log "Rebuilding and starting containers..."
    docker compose up -d --build 2>&1 | tee -a "$LOG_FILE"
    show_control_help
    ;;
  *)
    log "Usage: ./start.sh [dev|prod|logs|rebuild]"
    log "  dev      - Run in development mode (default)"
    log "  prod     - Run in production mode (detached)"
    log "  logs     - Show logs"
    log "  rebuild  - Rebuild and restart containers"
    exit 1
    ;;
esac