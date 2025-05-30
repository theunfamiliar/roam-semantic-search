#!/bin/bash

# Create log directories
mkdir -p logs/{server,deploy,audit,performance,data,search,test,coverage/{html,json}}

# Set appropriate permissions
chmod -R 755 logs

# Create empty log files to ensure they exist
touch logs/server/app.log
touch logs/server/error.log
touch logs/deploy/deploy.log
touch logs/audit/audit.log
touch logs/performance/perf.log
touch logs/data/operations.log
touch logs/search/queries.log
touch logs/test/pytest.log

echo "Log directories and files created successfully in logs/" 