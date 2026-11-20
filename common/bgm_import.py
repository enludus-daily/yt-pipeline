"""Turn a track generated with Audio Studio MCP (Stable Audio 3) into an app's BGM.

usage:
  python common/bgm_import.py <app> <generated.wav> --prompt "<the English prompt used>" [--model medium] [--seed N]

Writes apps/<app>/bgm.m4a (AAC 192k, -16 LUFS, 0.4 s fade in, 1.5 s fade out) and apps/<app>/bgm.json
({"source": "stable-audio-3", "prompt", "model", "seed", "seconds", "made"}).
compose.py loops the track if the video is longer, so a 40 s track is enough for a Short.
Only ffmpeg is needed (no numpy), so this also runs on the Mac that generates the music.
"""
import argparse, datetime, json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("app"); ap.add_argument("wav")
ap.add_argument("--prompt", required=True); ap.add_argument("--model", default="medium"); ap.add_argument("--seed", type=int)
o = ap.parse_args()

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", o.wav],
                           capture_output=True, text=True, check=True).stdout.strip())
out_dir = os.path.join(ROOT, "apps", o.app); os.makedirs(out_dir, exist_ok=True)
m4a = os.path.join(out_dir, "bgm.m4a")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", o.wav, "-af",
                f"loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.4,afade=t=out:st={max(dur - 1.5, 0):.2f}:d=1.5",
                "-ar", "48000", "-c:a", "aac", "-b:a", "192k", m4a], check=True)
meta = {"source": "stable-audio-3", "prompt": o.prompt, "model": o.model, "seed": o.seed, "seconds": round(dur, 2),
        "made": datetime.datetime.now().isoformat(timespec="seconds"),
        "license": "Stability AI Community License (generated locally with Audio Studio MCP)"}
json.dump(meta, open(os.path.join(out_dir, "bgm.json"), "w"), ensure_ascii=False, indent=2)
print(m4a)
