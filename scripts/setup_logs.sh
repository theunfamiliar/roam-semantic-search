#!/bin/bash

# Create log directories
mkdir -p logs/{server,deploy,audit,performance,data,search}

# Set appropriate permissions
chmod -R 755 logs

echo "Log directories created successfully in logs/" 