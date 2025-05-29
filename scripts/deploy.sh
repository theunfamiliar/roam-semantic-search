#!/bin/bash
set -e

# Get commit message from argument or use default
MESSAGE=${1:-"🚀 Deploying latest changes"}

echo "📦 Committing changes..."
git add .
if git diff-index --quiet HEAD; then
    echo "⚠️ No changes to commit"
else
    git commit -m "$MESSAGE"
    git push
fi

echo "🌐 Deploying to remote server..."
# Copy and execute deploy-remote.sh on the server
scp scripts/deploy-remote.sh root@207.180.227.18:/root/deploy-remote.sh
ssh root@207.180.227.18 'chmod +x /root/deploy-remote.sh && /root/deploy-remote.sh'

echo "✅ Deployment complete!" 