"""Compose a 1080x1920 "AI ships an app a day" Short from one app's demo recording.

usage: python daily/compose.py <demo.mp4> <icon.png> <outdir>
env (all text is English, written per app):
  DAY       day number in the series, e.g. 24
  NAME      app name, e.g. "Rolling Snake"
  HOOK      one line for the first 3 s: the problem or the mash-up, e.g. "Snake, but your body is the billiard cushion."
  TAGLINE   one short line under the name at the end, e.g. "A physics puzzle for iPhone"
  STORE     "Coming soon to the App Store" (default) or "Free on the App Store"
  VO        directory with hook.wav / demo.wav / outro.wav (narration; optional)
  ART_DIR   background art (default assets/gojuon-art; per-day art from Codex can replace it)
  SOUNDS    BGM directory with bgm.mp3 (optional; default assets/gojuon-sounds)
The demo is the app's own `-demo` playback recorded in CI (daily-actions ios-ci, artifact demo-video).
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

DEMO, ICON, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DAY = os.environ.get("DAY", "1"); NAME = os.environ.get("NAME", "Today's app")
HOOK = os.environ.get("HOOK", "An AI built this iPhone app in one day.")
TAGLINE = os.environ.get("TAGLINE", ""); STORE = os.environ.get("STORE", "Coming soon to the App Store")
VO = os.environ.get("VO", ""); ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ART_DIR = os.environ.get("ART_DIR", os.path.join(ROOT, "assets", "gojuon-art"))
SND = os.environ.get("SOUNDS", os.path.join(ROOT, "assets", "gojuon-sounds"))
W, H = 1080, 1920; BG = (234, 242, 247); INK = (16, 32, 48); ACCENT = (232, 122, 30); BLUE = (52, 138, 180)
F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
font = lambda w, s: ImageFont.truetype(F.format(w), s)
os.makedirs(OUT, exist_ok=True); p = lambda n: os.path.join(OUT, n)
def run(*a): subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def dur(f): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip() or 0)

def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    return lines + ([cur] if cur else [])
def center(d, y, text, f, fill, maxw=W - 160):
    for line in wrap(d, text, f, maxw):
        tw = d.textlength(line, font=f); d.text(((W - tw) / 2, y), line, font=f, fill=fill); y += f.size * 1.2
    return y
def pill(d, y, text, f, fg, bg):
    tw = d.textlength(text, font=f); pad = 34; h = f.size + 40
    d.rounded_rectangle(((W - tw) / 2 - pad, y, (W + tw) / 2 + pad, y + h), radius=h // 2, fill=bg)
    d.text(((W - tw) / 2, y + 16), text, font=f, fill=fg); return y + h
def art(i):
    arts = sorted(f for f in os.listdir(ART_DIR) if f.endswith(".png")) if os.path.isdir(ART_DIR) else []
    base = Image.new("RGBA", (W, H), BG + (255,))
    if arts: base.alpha_composite(Image.open(os.path.join(ART_DIR, arts[(int(DAY) + i) % len(arts)])).convert("RGBA").resize((W, H)))
    return base.convert("RGB")
def icon(size):
    ic = Image.open(ICON).convert("RGBA").resize((size, size)); m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size, size), radius=int(size * 0.22), fill=255); return ic, m

# 1) hook card
im = art(0); d = ImageDraw.Draw(im)
pill(d, 560, f"DAY {DAY}", font("Black", 56), (255, 255, 255), ACCENT)
d.rounded_rectangle((70, 700, W - 70, 1240), radius=56, fill=INK)
y = center(d, 760, HOOK, font("Black", 78), (255, 255, 255), W - 220)
center(d, max(y + 30, 1120), "An AI built it in one day.", font("SemiBold", 44), (255, 196, 140))
im.save(p("hook.png"))

# 2) demo overlay: caption band on top, phone recording below
dd = dur(DEMO); DW = 820; DY = 300
ov = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(ov)
center(d, 70, f"Day {DAY}: {NAME}", font("Black", 64), INK)
pill(d, 175, "Built by AI in ~1 day", font("Bold", 40), (255, 255, 255), ACCENT)
ov.save(p("ov_demo.png"))

# 3) outro card
o = art(1); d = ImageDraw.Draw(o); ic, m = icon(340); o.paste(ic, ((W - 340) // 2, 560), m)
y = center(d, 950, NAME, font("Black", 84), INK)
if TAGLINE: y = center(d, y + 10, TAGLINE, font("SemiBold", 46), (70, 90, 110))
y = pill(d, y + 40, STORE, font("Bold", 48), (255, 255, 255), BLUE)
center(d, y + 30, f"Day {int(DAY) + 1} drops tomorrow. Follow along!", font("SemiBold", 40), (90, 110, 130))
o.save(p("outro.png"))

ENC = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-an"]
def still(img, secs, out):
    run("ffmpeg", "-y", "-i", img, "-frames:v", str(int(secs * 30)), "-vf",
        f"scale={W}:{H},zoompan=z='min(zoom+0.0006,1.04)':d={int(secs * 30)}:s={W}x{H}:fps=30", *ENC, out)
def vo_len(name):
    f = os.path.join(VO, f"{name}.wav") if VO else ""
    return dur(f) if f and os.path.exists(f) else 0.0
# each card lasts at least 3 s, longer when its narration needs it
HOOK_S, OUTRO_S = max(3.0, vo_len("hook") + 0.7), max(3.0, vo_len("outro") + 0.9)
still(p("hook.png"), HOOK_S, p("s1.mp4"))
# the phone recording keeps its aspect ratio, fitted into DW x (H - DY - 60), with a soft shadow frame
run("ffmpeg", "-y", "-loop", "1", "-i", p("ov_demo.png"), "-i", DEMO, "-filter_complex",
    f"[1:v]scale={DW}:{H - DY - 60}:force_original_aspect_ratio=decrease,pad=iw+8:ih+8:4:4:color=0xD6E0E8,fps=30[ph];"
    f"[0:v][ph]overlay=(W-w)/2:{DY}:shortest=1", "-t", f"{dd:.2f}", *ENC, p("s2.mp4"))
still(p("outro.png"), OUTRO_S, p("s3.mp4"))
open(p("list.txt"), "w").write("file 's1.mp4'\nfile 's2.mp4'\nfile 's3.mp4'\n")
run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", p("list.txt"), "-c", "copy", p("video.mp4"))

total = HOOK_S + dd + OUTRO_S
ins = []; flt = []; n = 0
if os.path.exists(os.path.join(SND, "bgm.mp3")):
    ins += ["-stream_loop", "-1", "-i", os.path.join(SND, "bgm.mp3")]; n += 1
    flt.append(f"[1:a]atrim=0:{total:.2f},volume=0.20,afade=t=in:d=0.5,afade=t=out:st={total - 1.2:.2f}:d=1.2[m0]")
for name, st in (("hook", 0.3), ("demo", HOOK_S + 0.4), ("outro", HOOK_S + dd + 0.3)):
    f = os.path.join(VO, f"{name}.wav") if VO else ""
    if f and os.path.exists(f):
        ins += ["-i", f]; n += 1; ms = int(st * 1000)
        flt.append(f"[{n}:a]adelay={ms}|{ms}[m{n - 1}]")
if n:
    flt.append("".join(f"[m{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,alimiter=limit=0.95,apad[a]")
    run("ffmpeg", "-y", "-i", p("video.mp4"), *ins, "-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", p("short.mp4"))
else:
    run("ffmpeg", "-y", "-i", p("video.mp4"), "-c", "copy", p("short.mp4"))
print(p("short.mp4"))
