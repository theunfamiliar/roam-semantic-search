#!/bin/bash

set -e

# Ensure log directory exists
mkdir -p logs/cron

LOG="logs/cron/cron.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log_message() {
    echo "[$TIMESTAMP] $1" >> "$LOG"
    echo "$1"  # Also print to console
}

# Step 0: Safety fix – ensure scripts are executable
chmod +x ./scripts/*.sh

# Step 1: Import Graph
log_message "📥 Starting graph ingest..."
if python3 scripts/import_graph.py >> "$LOG" 2>&1; then
    log_message "✅ Graph import successful."
else
    log_message "❌ Graph import failed!"
    echo "Roam graph import failed at $TIMESTAMP" | mail -s "❌ Roam Import Failure" james@dunndealpr.com
    exit 1
fi

# Step 2: Search Health Check
log_message "🔍 Running search health check..."
if curl -s -o /dev/null -w "%{http_code}" -u admin:secret -H "Content-Type: application/json" \
    -d '{"query":"health","top_k":1}' http://localhost:8000/search | grep -q 200; then
    log_message "✅ Search verification succeeded."
else
    log_message "❌ Search verification failed!"
    echo "Search verification failed after graph import at $TIMESTAMP" | mail -s "❌ Search Health Check Failed" james@dunndealpr.com
    exit 1
fi

# Step 3: Semantic Health Check
log_message "🧠 Running semantic health check..."
SEMANTIC_STATUS=$(curl -s -w "%{http_code}" -o /dev/null -u admin:secret -H "Content-Type: application/json" \
    -d '{"query":"What do I believe about control?","top_k":3}' http://localhost:8000/semantic)

if [ "$SEMANTIC_STATUS" -eq 200 ]; then
    log_message "✅ Semantic endpoint verification succeeded."
else
    log_message "❌ Semantic endpoint failed with status $SEMANTIC_STATUS!"
    echo "Semantic verification failed at $TIMESTAMP (Status: $SEMANTIC_STATUS)" | mail -s "❌ Semantic Endpoint Failure" james@dunndealpr.com
    exit 1
fi

# Step 4: Auto-push latest graph export (if available)
if [ -d /root/roam-to-git/notes ]; then
  cd /root/roam-to-git/notes
  git add json/*.json
  if git diff --cached --quiet; then
    echo "ℹ️ [$TIMESTAMP] No new Roam JSON exports to push." >> "$LOG"
  else
    git commit -m "🕒 New export $TIMESTAMP" && git push
    echo "✅ [$TIMESTAMP] Roam JSON export pushed to GitHub." >> "$LOG"
  fi
  cd - > /dev/null
fi

log_message "✅ All checks completed successfully."