"""Per-app look: card backgrounds and accent colours come from the app itself, not from another app's art.
- background: a frame of the app's own footage, blurred and washed out
- accent: the most vivid colour of the app icon
"""
import colorsys, subprocess
from PIL import Image, ImageFilter

W, H = 1080, 1920

def frame_bg(video, at=None, wash=0.45):
    """Blurred, washed-out still from the app's own recording (cover-fit to 1080x1920)."""
    if at is None:
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                                 capture_output=True, text=True).stdout.strip() or 2)
        at = d * 0.45
    tmp = video + f".bg-{at:.2f}.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", video, "-frames:v", "1", tmp], check=True)
    im = Image.open(tmp).convert("RGB")
    s = max(W / im.width, H / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1))
    l, t = (im.width - W) // 2, (im.height - H) // 2; im = im.crop((l, t, l + W, t + H))
    im = im.filter(ImageFilter.GaussianBlur(28))
    return Image.blend(im, Image.new("RGB", (W, H), (248, 248, 248)), wash)

def accent(icon, default=(52, 138, 180)):
    """Most vivid, not-too-light colour in the icon."""
    try:
        im = Image.open(icon).convert("RGB").resize((64, 64))
    except Exception:
        return default
    best, score = default, -1
    for (r, g, b) in im.getdata():
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if 0.25 < l < 0.7 and s * (1 - abs(l - 0.5)) > score:
            best, score = (r, g, b), s * (1 - abs(l - 0.5))
    return best

def ink_on(rgb):
    """Readable text colour on top of rgb."""
    r, g, b = rgb; return (16, 32, 48) if (0.299 * r + 0.587 * g + 0.114 * b) > 165 else (255, 255, 255)
