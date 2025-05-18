#!/bin/bash

set -e

LOG="logs/cron.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "📥 [$TIMESTAMP] Starting graph ingest..." >> "$LOG"

# Step 0: Safety fix – ensure scripts are executable
chmod +x ./scripts/*.sh

# Step 1: Import Graph
if python3 scripts/import_graph.py >> "$LOG" 2>&1; then
  echo "✅ [$TIMESTAMP] Graph import successful." >> "$LOG"
else
  echo "❌ [$TIMESTAMP] Graph import failed!" >> "$LOG"
  echo "Roam graph import failed at $TIMESTAMP" | mail -s "❌ Roam Import Failure" james@dunndealpr.com
  exit 1
fi

# Step 2: Search Health Check
if curl -s -o /dev/null -w "%{http_code}" -u admin:secret -H "Content-Type: application/json" \
  -d '{"query":"health","top_k":1}' http://localhost:8000/search | grep -q 200; then
  echo "✅ [$TIMESTAMP] Search verification succeeded." >> "$LOG"
else
  echo "❌ [$TIMESTAMP] Search verification failed!" >> "$LOG"
  echo "Search verification failed after graph import at $TIMESTAMP" | mail -s "❌ Search Health Check Failed" james@dunndealpr.com
  exit 1
fi

# Step 3: Semantic Health Check
SEMANTIC_STATUS=$(curl -s -w "%{http_code}" -o /dev/null -u admin:secret -H "Content-Type: application/json" \
  -d '{"query":"What do I believe about control?","top_k":3}' http://localhost:8000/semantic)

if [ "$SEMANTIC_STATUS" -eq 200 ]; then
  echo "✅ [$TIMESTAMP] Semantic endpoint verification succeeded." >> "$LOG"
else
  echo "❌ [$TIMESTAMP] Semantic endpoint failed with status $SEMANTIC_STATUS!" >> "$LOG"
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

echo "✅ [$TIMESTAMP] All steps completed." >> "$LOG"