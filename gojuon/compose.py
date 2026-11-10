"""Compose a 1080x1920 Short from a recorded gojuon-minesweeper match.

usage: python compose_gojuon.py <rec.webm> <outdir> <icon.png>
Env: G0/GF/R1 timings (seconds in the recording), ANSWER, CLUE, CLUES, VO (narration dir).
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REC, OUT, ICON = sys.argv[1], sys.argv[2], sys.argv[3]
VO = os.environ.get("VO", "vo")
G0, GF, R1 = float(os.environ.get("G0", 3.4)), float(os.environ.get("GF", 10.7)), float(os.environ.get("R1", 13.3))
ANSWER = os.environ.get("ANSWER", "KETCHUP").upper()
CLUE = os.environ.get("CLUE") or "7 letters · a condiment"  # shown under the caption
CLUES = os.environ.get("CLUES", "3")  # how many cells were open when the bot answered
W, H = 1080, 1920
BG = (234, 242, 247); INK = (16, 32, 48); ACCENT = (232, 122, 30); BLUE = (52, 138, 180)
F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
font = lambda w, s: ImageFont.truetype(F.format(w), s)
os.makedirs(OUT, exist_ok=True)
p = lambda n: os.path.join(OUT, n)

def run(*a): subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def center(d, y, text, f, fill, w=W):
    for line in text.split("\n"):
        tw = d.textlength(line, font=f); d.text(((w - tw) / 2, y), line, font=f, fill=fill); y += f.size * 1.18
    return y

def pill(d, y, text, f, fg, bg):
    tw = d.textlength(text, font=f); pad = 34; h = f.size + 40
    d.rounded_rectangle(((W - tw) / 2 - pad, y, (W + tw) / 2 + pad, y + h), radius=h // 2, fill=bg)
    d.text(((W - tw) / 2, y + 16), text, font=f, fill=fg)

# frame grabs
run("ffmpeg", "-y", "-ss", str(GF), "-i", REC, "-frames:v", "1", p("freeze.png"))
run("ffmpeg", "-y", "-ss", str(R1 - 0.3), "-i", REC, "-frames:v", "1", p("result.png"))

# layout: game area cropped to top 1760px, scaled 0.86, placed under a caption band
SC = 0.86; GW, GH = int(W * SC), int(1760 * SC); GX, GY = (W - GW) // 2, 330

def frame_overlay(name, caption, sub=None, big=None):
    im = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(im)
    im.paste((0, 0, 0, 0), (GX, GY, GX + GW, GY + GH))  # hole for the video
    y = center(d, 80, caption, font("Black", 66), INK)
    if sub: pill(d, y + 18, sub, font("Bold", 40), (255, 255, 255), ACCENT)
    if big:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle((90, 860, W - 90, 1240), radius=48, fill=(16, 32, 48, 235))
        center(od, 905, big[0], font("Black", 104), (255, 255, 255)); center(od, 1060, big[1], font("Bold", 64), ACCENT)
        im = Image.alpha_composite(im, ov)
    im.save(p(name))

frame_overlay("ov_game.png", "Can you beat the bot?", CLUE)
frame_overlay("ov_pause.png", "Pause & guess!", CLUE)
for n in "321":
    frame_overlay(f"ov_pause{n}.png", f"Pause & guess!  {n}", CLUE)
frame_overlay("ov_result.png", "The bot got it!", None, (ANSWER, "Did you beat it?"))
HOOK_N = CLUES if CLUES.isdigit() else "a few"

# background art (generated with Codex, assets/gojuon-art/bg-0N.png); ART_INDEX picks one, e.g. seed % 3
ART_DIR = os.environ.get("ART_DIR", os.path.join(os.path.dirname(__file__), "..", "assets", "gojuon-art"))
ARTS = sorted(f for f in os.listdir(ART_DIR) if f.endswith(".png")) if os.path.isdir(ART_DIR) else []
def art(shift=0):
    if not ARTS:
        return Image.new("RGB", (W, H), BG)
    f = ARTS[(int(os.environ.get("ART_INDEX", "0")) + shift) % len(ARTS)]
    a = Image.open(os.path.join(ART_DIR, f)).convert("RGBA").resize((W, H))
    base = Image.new("RGBA", (W, H), BG + (255,)); base.alpha_composite(a)
    return base.convert("RGB")

# hook card: background art + headline
bg = art(); d = ImageDraw.Draw(bg)
d.rounded_rectangle((70, 640, W - 70, 1260), radius=56, fill=INK)
center(d, 700, f"This bot guessed\nthe word from\njust {HOOK_N} clues.", font("Black", 92), (255, 255, 255))
pill(d, 1120, "Can you do better?", font("Bold", 46), (255, 255, 255), ACCENT)
bg.save(p("hook.png"))

# outro card
o = art(1); d = ImageDraw.Draw(o)
ic = Image.open(ICON).convert("RGBA").resize((360, 360)); m = Image.new("L", (360, 360), 0)
ImageDraw.Draw(m).rounded_rectangle((0, 0, 360, 360), radius=80, fill=255); o.paste(ic, ((W - 360) // 2, 600), m)
y = center(d, 1010, "Gojuon Minesweeper", font("Black", 84), INK)
y = center(d, y + 20, "A word-guessing minesweeper\nin English & Japanese", font("SemiBold", 48), (70, 90, 110))
pill(d, y + 40, "Free on the App Store", font("Bold", 52), (255, 255, 255), BLUE)
center(d, y + 150, "Link in description", font("SemiBold", 40), (90, 110, 130))
o.save(p("outro.png"))

ENC = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-an"]
def still(img, dur, out):
    run("ffmpeg", "-y", "-i", img, "-frames:v", str(int(dur*30)), "-vf", f"scale={W}:{H},zoompan=z='min(zoom+0.0006,1.04)':d={int(dur*30)}:s={W}x{H}:fps=30", *ENC, out)
def game(ss, to, ov, out, freeze=False):
    src = ["-loop", "1", "-t", str(to), "-i", p("freeze.png")] if freeze else ["-ss", str(ss), "-to", str(to), "-i", REC]
    run("ffmpeg", "-y", *src, "-i", ov, "-filter_complex",
        f"[0:v]crop={W}:1760:0:0,scale={GW}:{GH},fps=30[g];color=c=0xEAF2F7:s={W}x{H}:r=30[bg];[bg][g]overlay={GX}:{GY}:shortest=1[v];[v][1:v]overlay=0:0", *ENC, out)

still(p("hook.png"), 2.8, p("s1.mp4"))
game(G0, GF, p("ov_game.png"), p("s2.mp4"))
game(0, 1.0, p("ov_pause.png"), p("s3_go.mp4"), freeze=True)
for n in "321": game(0, 1.0, p(f"ov_pause{n}.png"), p(f"s3_{n}.mp4"), freeze=True)
game(GF + 0.1, R1, p("ov_result.png"), p("s4.mp4"))
still(p("outro.png"), 2.8, p("s5.mp4"))
parts = ["s1", "s2", "s3_go", "s3_3", "s3_2", "s3_1", "s4", "s5"]
open(p("list.txt"), "w").write("".join(f"file '{x}.mp4'\n" for x in parts))
run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", p("list.txt"), "-c", "copy", p("video.mp4"))

# audio: narration + in-game sounds (synthesized by the app's scripts/sounds/make_sounds.py)
SND = os.environ.get("SOUNDS", os.path.join(os.path.dirname(__file__), "..", "assets", "gojuon-sounds"))
d2, d3 = GF - G0, 4.0
t_pause = 2.8 + d2; t_reveal = t_pause + d3; t_outro = t_reveal + (R1 - GF - 0.1)
cues = [  # (file, start seconds, volume)
    (os.path.join(VO, "hook.wav"), 0.25, 1.0),
    (os.path.join(VO, "game.wav"), 2.8 + 0.3, 1.0),
    (os.path.join(VO, "pause.wav"), t_pause + 0.05, 1.0),
    (os.path.join(VO, "three.wav"), t_pause + 1.0, 1.0),
    (os.path.join(VO, "two.wav"), t_pause + 2.0, 1.0),
    (os.path.join(VO, "one.wav"), t_pause + 3.0, 1.0),
    (os.path.join(SND, "tap.mp3"), t_pause + 1.0, 0.8),
    (os.path.join(SND, "tap.mp3"), t_pause + 2.0, 0.8),
    (os.path.join(SND, "tap.mp3"), t_pause + 3.0, 0.8),
    (os.path.join(SND, "correct.mp3"), t_reveal, 0.8),
    (os.path.join(VO, "reveal.wav"), t_reveal + 0.35, 1.0),
    (os.path.join(VO, "outro.wav"), t_outro + 0.3, 1.0),
]
total = t_outro + 2.8
ins = ["-stream_loop", "-1", "-i", os.path.join(SND, "bgm.mp3")]
# BGM: quiet under the voice, dips during the countdown, fades out at the end
flt = [f"[1:a]atrim=0:{total:.2f},volume='if(between(t,{t_pause:.2f},{t_reveal:.2f}),0.10,0.22)':eval=frame,"
       f"afade=t=in:d=0.5,afade=t=out:st={total-1.2:.2f}:d=1.2[bgm]"]
for i, (f, st, vol) in enumerate(cues):
    ins += ["-i", f]; ms = int(st * 1000)
    flt.append(f"[{i+2}:a]volume={vol},adelay={ms}|{ms}[c{i}]")
flt.append("[bgm]" + "".join(f"[c{i}]" for i in range(len(cues))) + f"amix=inputs={len(cues)+1}:normalize=0,alimiter=limit=0.95,apad[a]")
run("ffmpeg", "-y", "-i", p("video.mp4"), *ins, "-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[a]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", p("short.mp4"))
print(p("short.mp4"))
