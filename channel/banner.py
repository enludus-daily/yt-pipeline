"""YouTube channel banner 2560x1440. Text stays inside the 1546x423 safe area (visible on every device)."""
import os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 2560, 1440; BG = (234, 242, 247); INK = (16, 32, 48); ACCENT = (232, 122, 30)
F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"; font = lambda w, s: ImageFont.truetype(F.format(w), s)
art = os.path.join(ROOT, "assets", "gojuon-art")
a1 = Image.open(os.path.join(art, "bg-01.png")).convert("RGBA")   # tiles top-left / bottom-right
a3 = Image.open(os.path.join(art, "bg-03.png")).convert("RGBA")
BG = a1.convert("RGB").getpixel((540, 960))   # match the art's own background so no seams show
im = Image.new("RGBA", (W, H), BG + (255,))
# place the tile clusters left and right of the safe area
# tile clusters sit left and right of the safe area (x < 507 and x > 2053), never under the text
im.alpha_composite(a1.crop((0, 0, 620, 560)).resize((440, 397)), (40, (H - 397) // 2 - 60))
im.alpha_composite(a3.crop((620, 0, 1080, 560)).resize((330, 402)), (W - 330 - 60, (H - 402) // 2 - 80))
im.alpha_composite(a3.crop((0, 1240, 640, 1920)).resize((440, 467)), (W - 440 - 40, (H - 467) // 2 + 260))
d = ImageDraw.Draw(im)
sx, sy, sw, sh = (W - 1546) // 2, (H - 423) // 2, 1546, 423
def c(y, t, f, fill):
    tw = d.textlength(t, font=f); d.text((sx + (sw - tw) / 2, y), t, font=f, fill=fill)
c(sy + 20, "An AI ships a new iPhone app every day", font("Black", 74), INK)
c(sy + 130, "Indie games · word puzzles · Day 1, 2, 3 …", font("SemiBold", 52), (70, 90, 110))
t = "New Shorts daily"; f = font("Bold", 50); tw = d.textlength(t, font=f); h = 50 + 44
x0 = sx + (sw - tw) / 2 - 40; y0 = sy + 250
d.rounded_rectangle((x0, y0, x0 + tw + 80, y0 + h), radius=h // 2, fill=ACCENT); d.text((x0 + 40, y0 + 18), t, font=f, fill=(255, 255, 255))
out = os.path.join(ROOT, "channel", "banner-2560x1440.png"); im.convert("RGB").save(out); print(out)
# preview with the safe area outlined (not for upload)
pv = im.convert("RGB"); ImageDraw.Draw(pv).rectangle((sx, sy, sx + sw, sy + sh), outline=(255, 0, 0), width=4)
pv.resize((1280, 720)).save(os.path.join(ROOT, "channel", "banner-preview-safe-area.png"))
