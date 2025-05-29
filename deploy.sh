#!/bin/bash
set -e

MESSAGE=${1:-"🚀 Deploying latest changes"}

echo "🔧 Committing local changes..."
git add .
if git diff-index --quiet HEAD; then
  echo "⚠️ Nothing to commit."
else
  git commit -m "$MESSAGE"
  git push
fi

echo "🌐 SSHing into VPS to deploy..."
scp scripts/deploy-remote.sh root@207.180.227.18:/root/deploy-remote.sh
ssh root@207.180.227.18 'chmod +x /root/deploy-remote.sh && /root/deploy-remote.sh'