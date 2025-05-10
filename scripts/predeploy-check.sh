#!/bin/bash

# ───────────────────────────────────────────────
# 🔍 Pre-Deployment Sanity Checks
# ───────────────────────────────────────────────

# 1. Check for uncommitted changes
echo -n "🔄 Checking for uncommitted changes... "
if [[ -n $(git status --porcelain) ]]; then
  echo "❌ Found. Please commit or stash first."
  exit 1
else
  echo "✅ Clean."
fi

# 2. Check for .env file
echo -n "🔐 Checking for .env file... "
if [[ ! -f .env ]]; then
  echo "❌ Missing .env"
  exit 1
else
  echo "✅ Found"
fi

# 3. Ensure .env and venv are gitignored
echo -n "🛡️  Verifying .gitignore covers .env and venv... "
grep -qE '^\.env$' .gitignore && grep -qE '^venv/$' .gitignore && echo "✅ OK" || { echo "❌ .gitignore missing entries"; exit 1; }

# 4. Check branch is main
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -n "🌿 Confirming branch is main... "
if [[ "$BRANCH" != "main" ]]; then
  echo "❌ On '$BRANCH' not 'main'"
  exit 1
else
  echo "✅ OK"
fi

# 5. Check local is in sync with remote
echo -n "📡 Checking if local is up-to-date with origin/main... "
git fetch origin >/dev/null 2>&1
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse origin/main)
if [[ "$LOCAL" != "$REMOTE" ]]; then
  echo "❌ Local and origin/main differ"
  exit 1
else
  echo "✅ Synced"
fi

# 6. Check SSH key auth to GitHub
echo -n "🔐 Testing SSH to GitHub... "
ssh -T git@github.com -o BatchMode=yes -o ConnectTimeout=5 2>&1 | grep -q "successfully authenticated" && echo "✅ OK" || { echo "❌ SSH to GitHub failed"; exit 1; }

# 7. Run flake8
if command -v flake8 >/dev/null 2>&1; then
  echo "🧹 Running flake8 lint checks..."
  flake8 . || { echo "❌ flake8 issues found"; exit 1; }
else
  echo "⚠️  flake8 not installed. Skipping lint checks."
fi

# 8. (Optional) Run black in check mode
if command -v black >/dev/null 2>&1; then
  echo "🧱 Checking formatting with black..."
  black . --check || { echo "❌ Code not formatted"; exit 1; }
else
  echo "⚠️  black not installed. Skipping format check."
fi

# 9. (Optional) Run unit tests
if command -v pytest >/dev/null 2>&1; then
  echo "🧪 Running unit tests..."
  pytest || { echo "❌ Tests failed"; exit 1; }
else
  echo "⚠️  pytest not installed. Skipping tests."
fi

echo "✅ All pre-deploy checks passed. You're good to go."
exit 0
