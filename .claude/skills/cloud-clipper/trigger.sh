#!/bin/bash
# trigger.sh <stream_url> [num_clips]
# Starts the GitHub Actions workflow and waits for it to finish.
# Requires: gh CLI installed and logged in (gh auth login)
set -e

URL="$1"
N="${2:-8}"
WORKFLOW="cloud-clipper.yml"
REPO="${GH_REPO:-$(git remote get-url origin 2>/dev/null | sed 's|https://github.com/||; s|\.git$||')}"
if [ -z "$REPO" ]; then
  echo "No remote found. Set GH_REPO=owner/repo and try again."
  exit 1
fi

echo "🚀 Starting cloud-clipper workflow on $REPO for: $URL"
RUN_ID=$(gh workflow run "$WORKFLOW" --repo "$REPO" \
  --field stream_url="$URL" \
  --field num_clips="$N" \
  --json id --jq '.id')

echo "Workflow run ID: $RUN_ID"
echo "Polling for completion..."

# Poll until the run finishes
while true; do
  STATUS=$(gh run view "$RUN_ID" --repo "$REPO" --json status --jq '.status')
  CONCLUSION=$(gh run view "$RUN_ID" --repo "$REPO" --json conclusion --jq '.conclusion')
  echo "  Status: $STATUS"
  if [ "$STATUS" = "completed" ]; then
    echo "Run finished with conclusion: $CONCLUSION"
    break
  fi
  sleep 10
done

echo "📥 Downloading finished shorts..."
gh run download "$RUN_ID" --repo "$REPO" -d "C:/claudepro/clipping-project/output/final"
echo "✓ Shorts downloaded to C:/claudepro/clipping-project/output/final/"
