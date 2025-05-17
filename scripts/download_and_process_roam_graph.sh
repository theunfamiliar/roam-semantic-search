#!/bin/bash

set -e

LOG="logs/cron.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "📥 [$TIMESTAMP] Starting graph ingest..." >> "$LOG"

if python3 scripts/import_graph.py >> "$LOG" 2>&1; then
  echo "✅ [$TIMESTAMP] Graph import successful." >> "$LOG"
else
  echo "❌ [$TIMESTAMP] Graph import failed!" >> "$LOG"
  echo "Roam graph import failed at $TIMESTAMP" | mail -s "❌ Roam Import Failure" james@dunndealpr.com
  exit 1
fi

if curl -s -o /dev/null -w "%{http_code}" -u admin:secret -H "Content-Type: application/json" \
  -d '{"query":"health","top_k":1}' http://localhost:8000/search | grep -q 200; then
  echo "✅ [$TIMESTAMP] Search verification succeeded." >> "$LOG"
else
  echo "❌ [$TIMESTAMP] Search verification failed!" >> "$LOG"
  echo "Search verification failed after graph import at $TIMESTAMP" | mail -s "❌ Search Health Check Failed" james@dunndealpr.com
  exit 1
fi

echo "✅ [$TIMESTAMP] All steps completed." >> "$LOG"
