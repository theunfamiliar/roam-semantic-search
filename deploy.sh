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
scp ./scripts/deploy-remote.sh singularity:/root/roam-semantic-search/scripts/deploy-remote.sh

# ⬅️ This line is the fix: use -t -t to force pseudo-terminal
ssh -t -t singularity << 'EOF'
  cd /root/roam-semantic-search
  chmod +x scripts/deploy-remote.sh
  ./scripts/deploy-remote.sh
EOF