"""frames/NNNNN.jpg + frames/times.json (seconds) -> constant-30fps mp4."""
import json, os, subprocess, sys
d, out = sys.argv[1], sys.argv[2]
t = json.load(open(os.path.join(d, "times.json")))
lines = []
for i, s in enumerate(t):
    dur = (t[i + 1] - s) if i + 1 < len(t) else 0.5
    lines += [f"file '{os.path.abspath(os.path.join(d, f'{i:05d}.jpg'))}'", f"duration {dur:.4f}"]
lines.append(lines[-2])  # concat demuxer needs the last file repeated
open(os.path.join(d, "concat.txt"), "w").write("\n".join(lines) + "\n")
# shift so the video starts at t[0] (frames before the first capture are absent)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(d, "concat.txt"),
                "-vf", f"tpad=start_duration={t[0]:.3f}:start_mode=clone,fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "16", out], check=True)
print(out)
