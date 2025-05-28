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
ssh -t singularity "bash /root/roam-semantic-search/scripts/deploy-remote.sh" \
  && echo -e "\033[1;32m✅ DEPLOY SUCCESSFUL\033[0m" \
  || echo -e "\033[1;31m❌ DEPLOY FAILED\033[0m"