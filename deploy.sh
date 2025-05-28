#!/bin/bash

set -e

print() {
  echo -e "\033[1;36m$1\033[0m"
}

COMMIT_MSG="${1:-.}"

print "🔧 Committing local changes..."
git add .
git commit -m "$COMMIT_MSG" || echo "⚠️ Nothing to commit."
git push origin main

print "🌐 SSHing into VPS to deploy..."
DEPLOY_OUTPUT=$(ssh -tt singularity << 'EOF'
  set -e
  cd /root/roam-semantic-search
  chmod +x ./scripts/*.sh
  git fetch origin
  git reset --hard origin/main
  if [ ! -f server.py ]; then echo "❌ server.py not found"; exit 1; fi
  systemctl stop semantic-api.service
  pkill -f uvicorn || true
  sleep 2
  if lsof -i :8000; then echo "❌ Port 8000 in use"; exit 1; fi
  systemctl start semantic-api.service
  sleep 3
  attempts=0
  until curl -s -f http://localhost:8000/ > /dev/null; do
    ((attempts++))
    if [ $attempts -ge 10 ]; then echo "❌ API not responding"; exit 1; fi
    sleep 1
  done
  echo "✅ DEPLOY SUCCESSFUL"
EOF
)

if echo "$DEPLOY_OUTPUT" | grep -q "✅ DEPLOY SUCCESSFUL"; then
  print "🎉 DEPLOY CONFIRMED: Everything is okay."
else
  echo "$DEPLOY_OUTPUT"
  echo "❌ Deploy may have failed. Check logs manually."
  exit 1
fi