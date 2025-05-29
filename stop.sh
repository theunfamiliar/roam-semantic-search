#!/bin/bash

# Set error handling
set -e

# Function to log messages with timestamps
log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if containers are running
check_containers() {
    if ! docker compose ps --quiet 2>/dev/null; then
        log_message "No containers are currently running."
        exit 0
    fi
}

# Main script
log_message "Stopping Roam Semantic Search services..."

# Check if containers exist
check_containers

# Stop containers gracefully
log_message "Stopping Docker containers..."
docker compose down --remove-orphans

log_message "All services stopped successfully." 