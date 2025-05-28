#!/bin/bash

set -e

print() {
  echo -e "\033[1;36m$1\033[0m"
}

# Optional commit message
COMMIT_MSG="${1:-.}"

print "🔧 Committing local changes..."
git add .
git commit -m "$COMMIT_MSG" || echo "⚠️ Nothing to commit."
git push origin main

print "🌐 SSHing into VPS to deploy..."
scp ./scripts/deploy-remote.sh singularity:/root/roam-semantic-search/scripts/deploy-remote.sh
ssh -tt singularity 'bash -l -c "cd /root/roam-semantic-search && ./scripts/deploy-remote.sh"'