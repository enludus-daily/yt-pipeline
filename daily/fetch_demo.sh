#!/usr/bin/env bash
# Download the newest demo video, app icon and README of one daily app.
# usage: daily/fetch_demo.sh <repo>   e.g. app-20261111-something  (owner: enludus-daily)
# Needs gh signed in with read access to the repo (Actions artifacts need a token even on public repos).
# Output: work/daily/<repo>/{demo.mp4, icon.png, README.md}
set -euo pipefail
REPO="enludus-daily/$1"
HERE=$(cd "$(dirname "$0")/.." && pwd)
OUT="$HERE/work/daily/$1"
rm -rf "$OUT"; mkdir -p "$OUT"
# newest successful CI run on main that uploaded a demo-video artifact
run=""
for id in $(gh api "repos/$REPO/actions/workflows/ci.yml/runs?branch=main&status=success&per_page=10" --jq '.workflow_runs[].id'); do
  if gh api "repos/$REPO/actions/runs/$id/artifacts" --jq '.artifacts[].name' | grep -qx demo-video; then run=$id; break; fi
done
[ -n "$run" ] || { echo "no successful CI run with a demo-video artifact in $REPO" >&2; exit 2; }
gh run download "$run" --repo "$REPO" --name demo-video --dir "$OUT/artifact"
video=$(find "$OUT/artifact" -name 'demo-*.mp4' -size +10k | head -1)
[ -n "$video" ] || { echo "the demo-video artifact has no video (the app may not support -demo yet)" >&2; exit 3; }
mv "$video" "$OUT/demo.mp4"
gh api "repos/$REPO/contents/App/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png" --jq .content | base64 -d > "$OUT/icon.png" || true
gh api "repos/$REPO/contents/README.md" --jq .content | base64 -d > "$OUT/README.md" || true
echo "run $run → $OUT"; ls -l "$OUT"
