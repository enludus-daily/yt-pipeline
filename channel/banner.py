"""YouTube channel banner 2560x1440 in the Enludus brand (navy, light blue, orange — the logo's colours).
No app's own art here: the channel covers many apps. Text stays inside the 1546x423 safe area."""
import os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 2560, 1440; NAVY = (7, 17, 29); BLUE = (146, 221, 255); ORANGE = (255, 155, 97)
F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"; font = lambda w, s: ImageFont.truetype(F.format(w), s)
im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
# soft light-blue dots, like a quiet grid, fading toward the centre
for y in range(40, H, 80):
    for x in range(40, W, 80):
        dist = abs(x - W / 2) / (W / 2)
        if dist > 0.55: d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=tuple(int(NAVY[i] + (BLUE[i] - NAVY[i]) * 0.25 * dist) for i in range(3)))
sx, sy, sw, sh = (W - 1546) // 2, (H - 423) // 2, 1546, 423
# the E mark (same shape as the favicon), left of the text
u = 6.2; ex, ey = sx + 10, sy + 70
d.polygon([(ex + a * u, ey + b * u) for a, b in [(0, 0), (29, 0), (29, 8), (9, 8), (9, 15), (26, 15), (26, 23), (9, 23), (9, 30), (29, 30), (29, 38), (0, 38)]], fill=BLUE)
d.ellipse((ex + 24 * u, ey - 5 * u, ex + 34 * u, ey + 5 * u), fill=ORANGE)
tx = ex + 260
d.text((tx, sy + 40), "An AI ships a new iPhone app", font=font("Black", 76), fill=(255, 255, 255))
d.text((tx, sy + 135), "every day", font=font("Black", 76), fill=BLUE)
d.text((tx, sy + 255), "Indie games, little tools, word puzzles · Day 1, 2, 3 …", font=font("SemiBold", 44), fill=(170, 190, 210))
out = os.path.join(ROOT, "channel", "banner-2560x1440.png"); im.save(out); print(out)
pv = im.copy(); ImageDraw.Draw(pv).rectangle((sx, sy, sx + sw, sy + sh), outline=(255, 0, 0), width=4)
pv.resize((1280, 720)).save(os.path.join(ROOT, "channel", "banner-preview-safe-area.png"))
