#!/usr/bin/env bash
# One Short from a seeded vs-bot match on the English board.
# usage: gojuon/make_short.sh <seed> [G0 GF R1]
#   Without timings they come from record.js's MARK lines:
#     G0 = board + 0.2 (board appears), GF = over_exact - 0.45 (bot thinking before its winning guess),
#     R1 = over + 2.3 (end of the result screen).
#   The answer and the clue ("7 letters · a condiment") are read from the finished match.
# env: CLUES (cells open when the bot answered; default "a few"), GAME_URL, LEVEL, ICON
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd); cd "$HERE"
SEED=$1
mkdir -p work/vo output
LOGF=work/record-$SEED.log
(cd work && node ../gojuon/record.js "$SEED" "" record) > "$LOGF"
grep -E "MARK" "$LOGF" || true
mark() { awk -v n="$1" '$1=="MARK" && $2==n {print $3}' "$LOGF"; }
if [ $# -ge 4 ]; then export G0=$2 GF=$3 R1=$4; else
  B=$(mark board); O=$(mark over_exact); O=${O:-$(mark over)}
  export G0=$(python3 -c "print(round($B+0.2,2))") GF=$(python3 -c "print(round($O-0.45,2))") R1=$(python3 -c "print(round($O+2.3,2))")
fi
INFO=$(tail -1 "$LOGF")
if ! grep -q "Bot (.*) got it" <<<"$INFO"; then echo "the bot did not win this match; pick another seed: $INFO" >&2; exit 2; fi
export ANSWER=$(grep -oP 'Answer: \K[a-z -]+' <<<"$INFO" | sed 's/ *$//')
N=$(grep -oP '^\d+(?=-letter word)' <<<"$INFO")
CAT=$(grep -oP 'letter word · \K[^|]+' <<<"$INFO" | sed 's/ *$//')
export CLUE="${CLUE:-$N letters · $CAT}" CLUES="${CLUES:-a few}" VO=work/vo
echo "seed=$SEED answer=$ANSWER clue='$CLUE' G0=$G0 GF=$GF R1=$R1"
.venv/bin/python common/frames_to_video.py work/frames work/rec.mp4
common/tts.sh work/vo/hook.wav "This bot guessed the word from just $CLUES clues."
common/tts.sh work/vo/game.wav "${GAME_LINE:-$N letters. Category: $CAT. Can you beat it?}"
common/tts.sh work/vo/pause.wav "Pause and guess!"
common/tts.sh work/vo/three.wav "Three."
common/tts.sh work/vo/two.wav "Two."
common/tts.sh work/vo/one.wav "One."
common/tts.sh work/vo/reveal.wav "$ANSWER!"
common/tts.sh work/vo/outro.wav "Gojuon Minesweeper. Free on the App Store."
rm -rf work/out
.venv/bin/python gojuon/compose.py work/rec.mp4 work/out "${ICON:-assets/gojuon-icon.png}"
cp work/out/short.mp4 "output/gojuon-${SEED}-${ANSWER// /-}.mp4"
echo "output/gojuon-${SEED}-${ANSWER// /-}.mp4"
