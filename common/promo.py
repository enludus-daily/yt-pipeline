"""Compose a 1080x1920 app promo Short from a screen recording and a JSON spec.

usage: python common/promo.py <spec.json> <outdir>

spec (paths are relative to the spec file):
{
  "recording": "rec.mp4",            # 1080x1920 screen recording (e.g. from a Playwright frame recorder)
  "icon": "icon.png",                # optional
  "hook": {"text": "Lost in Osaka's underground maze?", "sub": "There's a map for that", "secs": 3.0},
  "segments": [                      # parts of the recording, each with its own caption
    {"from": 4.4, "to": 9.4, "caption": "Search any shop, exit, or spot"}
  ],
  "outro": {"name": "Umeda Underground Navi", "lines": ["Free web app · 10 languages"], "pill": "umeda.enludus.com", "secs": 3.2},
  "voice": {"name": "af_bella", "speed": 1.06,
            "lines": [{"at": "hook", "text": "..."}, {"at": 0, "text": "..."}, {"at": "outro", "text": "..."}]},
                                     # at: "hook" / "outro" / segment index. Needs Kokoro (.cache/kokoro, common/kokoro_say.py)
  "bgm": "music.m4a",       # optional: the app's OWN music only (ducked under the voice). No other app's music
  "art": "bg.png",          # optional: the app's OWN art. Default: a blurred frame of the recording
  "accent": [r, g, b]       # optional. Default: the most vivid colour of the icon
}
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from look import frame_bg, accent, ink_on

SPEC, OUT = sys.argv[1], sys.argv[2]
spec = json.load(open(SPEC)); base = os.path.dirname(os.path.abspath(SPEC))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rel = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
W, H = 1080, 1920; BG = (234, 242, 247); INK = (16, 32, 48); ACCENT = (232, 122, 30); BLUE = (52, 138, 180)
F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
# Japanese text needs a Japanese font (Zen Kaku Gothic New, OFL, in assets/fonts). "lang": "ja" in the spec switches to it
FJ = os.path.join(ROOT, "assets", "fonts", "ZenKakuGothicNew-{}.ttf"); JA_W = {"Black": "Black", "Bold": "Bold", "SemiBold": "Bold", "Regular": "Medium"}
def font(w, s):
    if spec.get("lang") == "ja": return ImageFont.truetype(FJ.format(JA_W.get(w, "Bold")), s)
    return ImageFont.truetype(F.format(w), s)
os.makedirs(OUT, exist_ok=True); p = lambda n: os.path.join(OUT, n)
def run(*a): subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def dur(f): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip() or 0)

def wrap(d, text, f, maxw):
    out, cur = [], ""
    if " " not in text.strip():  # Japanese: no spaces, wrap by characters (\n forces a break)
        for part in text.split("\n"):
            cur = ""
            for ch in part:
                if d.textlength(cur + ch, font=f) <= maxw: cur += ch
                else: out.append(cur); cur = ch
            out.append(cur)
        return out
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: out.append(cur); cur = w
    return out + ([cur] if cur else [])
def center(d, y, text, f, fill, maxw=W - 140):
    for line in wrap(d, text, f, maxw):
        tw = d.textlength(line, font=f); d.text(((W - tw) / 2, y), line, font=f, fill=fill); y += f.size * 1.2
    return y
def pill(d, y, text, f, fg, bg):
    tw = d.textlength(text, font=f); pad = 34; h = f.size + 40
    d.rounded_rectangle(((W - tw) / 2 - pad, y, (W + tw) / 2 + pad, y + h), radius=h // 2, fill=bg)
    d.text(((W - tw) / 2, y + 16), text, font=f, fill=fg); return y + h
ACC = tuple(spec["accent"]) if spec.get("accent") else accent(rel(spec["icon"])) if spec.get("icon") else BLUE
def card_bg(at=None):
    # the app's own footage, blurred — never another app's art. "art" only when this app has its own
    if spec.get("art") and os.path.exists(rel(spec["art"])):
        im = Image.new("RGBA", (W, H), BG + (255,)); im.alpha_composite(Image.open(rel(spec["art"])).convert("RGBA").resize((W, H)))
        return im.convert("RGB")
    return frame_bg(rel(spec["recording"]), at)

# voice first: card lengths follow the narration
voice = spec.get("voice"); vo = {}
if voice:
    say = os.path.join(ROOT, "common", "kokoro_say.py")
    for i, ln in enumerate(voice["lines"]):
        f = p(f"vo-{i}.wav")
        subprocess.run([sys.executable, say, voice.get("name", "af_bella"), str(voice.get("speed", 1.06)), f, ln["text"]] + (["ja"] if spec.get("lang") == "ja" else []),
                       check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
        vo[i] = (ln["at"], f, dur(f))
def vo_len(at): return max([d for a, _, d in vo.values() if a == at] or [0])

hook, outro = spec["hook"], spec["outro"]
HOOK_S = max(hook.get("secs", 3.0), vo_len("hook") + 0.7)
OUTRO_S = max(outro.get("secs", 3.2), vo_len("outro") + 0.9)

im = card_bg(); d = ImageDraw.Draw(im)
d.rounded_rectangle((70, 660, W - 70, 1260), radius=56, fill=INK)
y = center(d, 720, hook["text"], font("Black", 84), (255, 255, 255), W - 220)
if hook.get("sub"): pill(d, max(y + 30, 1110), hook["sub"], font("Bold", 44), ink_on(ACC), ACC)
im.save(p("hook.png"))

o = card_bg(spec["segments"][-1]["to"] - 1.0); d = ImageDraw.Draw(o); y = 600
if spec.get("icon") and os.path.exists(rel(spec["icon"])):
    ic = Image.open(rel(spec["icon"])).convert("RGBA").resize((320, 320)); m = Image.new("L", (320, 320), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, 320, 320), radius=70, fill=255); o.paste(ic, ((W - 320) // 2, 560), m); y = 940
y = center(d, y, outro["name"], font("Black", 78), INK)
for line in outro.get("lines", []): y = center(d, y + 10, line, font("SemiBold", 46), (70, 90, 110))
if outro.get("pill"): pill(d, y + 40, outro["pill"], font("Bold", 50), ink_on(ACC), ACC)
o.save(p("outro.png"))

ENC = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-an"]
def still(img, secs, out):
    run("ffmpeg", "-y", "-i", img, "-frames:v", str(int(secs * 30)), "-vf",
        f"scale={W}:{H},zoompan=z='min(zoom+0.0006,1.04)':d={int(secs * 30)}:s={W}x{H}:fps=30", *ENC, out)
# screen recording: caption band on top, the phone screen scaled below it
SC = 0.82; GW, GH = int(W * SC), int(H * SC); GX, GY = (W - GW) // 2, H - GH - 40
parts = ["hook"]; still(p("hook.png"), HOOK_S, p("hook.mp4"))
seg_start = []; t = HOOK_S
for i, s in enumerate(spec["segments"]):
    ov = card_bg((s["from"] + s["to"]) / 2).convert("RGBA"); d = ImageDraw.Draw(ov)
    ov.paste((0, 0, 0, 0), (GX, GY, GX + GW, GY + GH))
    center(d, 70, s["caption"], font("Black", 62), INK, W - 120)
    ov.save(p(f"ov{i}.png"))
    run("ffmpeg", "-y", "-ss", str(s["from"]), "-to", str(s["to"]), "-i", rel(spec["recording"]), "-loop", "1", "-i", p(f"ov{i}.png"),
        "-filter_complex", f"[0:v]scale={GW}:{GH},fps=30[g];color=c=0xEAF2F7:s={W}x{H}:r=30[bg];[bg][g]overlay={GX}:{GY}:shortest=1[v];[v][1:v]overlay=0:0:shortest=1",
        *ENC, p(f"seg{i}.mp4"))
    seg_start.append(t); t += s["to"] - s["from"]; parts.append(f"seg{i}")
OUTRO_AT = t; still(p("outro.png"), OUTRO_S, p("outro.mp4")); parts.append("outro")
open(p("list.txt"), "w").write("".join(f"file '{x}.mp4'\n" for x in parts))
run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", p("list.txt"), "-c", "copy", p("video.mp4"))

total = OUTRO_AT + OUTRO_S; ins, flt, n = [], [], 0
for at, f, _ in vo.values():
    st = 0.3 if at == "hook" else OUTRO_AT + 0.3 if at == "outro" else seg_start[int(at)] + 0.3
    ins += ["-i", f]; n += 1; ms = int(st * 1000); flt.append(f"[{n}:a]aresample=48000,volume=1.5,adelay={ms}|{ms}[v{n}]")
if n:
    flt.append("".join(f"[v{k}]" for k in range(1, n + 1)) + f"amix=inputs={n}:normalize=0,apad,atrim=0:{total:.2f},asplit[vo1][vo2]")
bgm = spec.get("bgm")
if bgm and os.path.exists(rel(bgm)):
    ins += ["-stream_loop", "-1", "-i", rel(bgm)]; k = n + 1
    flt.append(f"[{k}:a]aresample=48000,atrim=0:{total:.2f},volume=0.55,afade=t=in:d=0.5,afade=t=out:st={total - 1.2:.2f}:d=1.2[m]")
    flt.append("[m][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck];[duck][vo2]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]" if n else "[m]anull[a]")
elif n:
    flt.append("[vo1]anull[a];[vo2]anullsink")
if flt:
    run("ffmpeg", "-y", "-i", p("video.mp4"), *ins, "-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", p("short.mp4"))
else:
    run("ffmpeg", "-y", "-i", p("video.mp4"), "-c", "copy", p("short.mp4"))
print(p("short.mp4"), round(total, 2))
