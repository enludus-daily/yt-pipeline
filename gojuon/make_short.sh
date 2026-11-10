#!/usr/bin/env bash
# One Short from a seeded match.
# usage: gojuon/make_short.sh <seed> <ANSWER> <G0> <GF> <R1>
#   G0 = board appears, GF = freeze (bot thinking before its winning guess), R1 = end of result
#   Find GF/R1 from the MARK lines printed by record.js (GF ≈ last open + 0.4, R1 ≈ over + 2.3).
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd); cd "$HERE"
SEED=$1 ANSWER=$2; export G0=$3 GF=$4 R1=$5 ANSWER VO=work/vo CLUE="${CLUE:-}" CLUES="${CLUES:-3}"
mkdir -p work/vo output
(cd work && node ../gojuon/record.js "$SEED" "" record | grep -E "MARK|Answer")
.venv/bin/python common/frames_to_video.py work/frames work/rec.mp4
common/tts.sh work/vo/hook.wav "This bot guessed the word from just ${CLUES:-3} clues."
common/tts.sh work/vo/game.wav "${GAME_LINE:-Can you beat it?}"
common/tts.sh work/vo/pause.wav "Pause and guess!"
common/tts.sh work/vo/reveal.wav "${ANSWER,,}!"
common/tts.sh work/vo/outro.wav "Gojuon Minesweeper. Free on the App Store."
.venv/bin/python gojuon/compose.py work/rec.mp4 work/out "${ICON:-assets/gojuon-icon.png}"
cp work/out/short.mp4 "output/gojuon-${SEED}-${ANSWER,,}.mp4"
