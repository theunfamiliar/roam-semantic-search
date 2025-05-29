#!/bin/bash

# Set error handling
set -e

# Function to log messages with timestamps
log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if scripts exist
check_scripts() {
    if [[ ! -f "stop.sh" ]]; then
        log_message "Error: stop.sh not found"
        exit 1
    fi
    if [[ ! -f "start.sh" ]]; then
        log_message "Error: start.sh not found"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    log_message "Usage: ./restart.sh [dev|prod|logs|rebuild]"
    log_message "  dev      - Run in development mode (default)"
    log_message "  prod     - Run in production mode (detached)"
    log_message "  logs     - Show logs"
    log_message "  rebuild  - Rebuild and restart containers"
    exit 1
}

# Get the mode from command line argument or default to dev
MODE=${1:-dev}

# Validate mode
case $MODE in
    "dev"|"prod"|"logs"|"rebuild")
        ;;
    *)
        show_usage
        ;;
esac

# Main script
log_message "Restarting Roam Semantic Search services in $MODE mode..."

# Check for required scripts
check_scripts

# Stop services
log_message "Stopping services..."
./stop.sh

# Small delay to ensure clean shutdown
sleep 2

# Start services with the specified mode
log_message "Starting services in $MODE mode..."
./start.sh "$MODE"

log_message "Restart completed successfully." 