#!/bin/bash
set -e

echo "🔧 Committing local changes..."
git add .
git commit -m "${1:-🔄 Deploying latest changes}" || echo "⚠️ Nothing to commit."
git push

echo "🌐 SSHing into VPS to deploy..."
scp scripts/deploy-remote.sh root@207.180.227.18:/root/roam-semantic-search/scripts/deploy-remote.sh
ssh -t root@207.180.227.18 "cd /root/roam-semantic-search && chmod +x scripts/deploy-remote.sh && ./scripts/deploy-remote.sh" && echo "✅ DEPLOY SUCCESS" || echo "❌ DEPLOY FAILED"