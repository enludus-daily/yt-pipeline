#!/usr/bin/env bash
# usage: common/tts.sh <out.wav> "<text>"   (Piper, English voice en_US-ryan-high)
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
VOICE="$HERE/.cache/voices/en_US-ryan-high.onnx"
if [ ! -f "$VOICE" ]; then
  mkdir -p "$(dirname "$VOICE")"
  for x in onnx onnx.json; do
    curl -sSL -o "$VOICE${x#onnx}" "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.$x"
  done
fi
echo "$2" | "$HERE/.venv/bin/piper" -m "$VOICE" -f "$1" 2>/dev/null
