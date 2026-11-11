"""Per-app background music, synthesized from scratch (no samples, so no licensing questions).

usage: python common/bgm.py <preset> <out.m4a> [seconds] [seed]
presets: see PRESETS below (one per app mood). Add a preset for a new app instead of reusing another app's music.

Each preset sets tempo, key, chord progression, the lead and pad instruments, and the drum pattern.
The melody is generated from the scale with a fixed seed, so the same preset always gives the same track.
Output is loudness-normalised to -20 LUFS (quiet enough to sit under narration).
"""
import os, subprocess, sys, tempfile, wave
import numpy as np

SR = 44100
PRESETS = {
    # Tamahebi: snake x billiards. Bouncy, playful, wooden "click" like balls hitting
    "tamahebi": dict(bpm=118, root=60, scale="major", prog=[0, 5, 3, 4], lead="marimba", pad="soft_square",
                     drums="bouncy", swing=0.12, lead_density=0.62, octave=12),
    # Umeda Underground Navi: walking through a busy station mall. Warm, light, steady footsteps
    "umeda": dict(bpm=102, root=62, scale="major_pent", prog=[0, 4, 5, 3], lead="epiano", pad="warm_pad",
                  drums="walk", swing=0.0, lead_density=0.45, octave=12),
    # calm study / tool apps
    "calm": dict(bpm=84, root=57, scale="minor_pent", prog=[0, 5, 3, 4], lead="epiano", pad="warm_pad",
                 drums="lofi", swing=0.18, lead_density=0.35, octave=12),
    # upbeat game
    "arcade": dict(bpm=132, root=64, scale="major", prog=[0, 3, 4, 4], lead="pluck", pad="soft_square",
                   drums="four", swing=0.0, lead_density=0.7, octave=12),
}
SCALES = {"major": [0, 2, 4, 5, 7, 9, 11], "major_pent": [0, 2, 4, 7, 9], "minor_pent": [0, 3, 5, 7, 10]}
CHORD_STEPS = {"major": [0, 2, 4], "major_pent": [0, 2, 3], "minor_pent": [0, 1, 3]}

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def env(n, a=0.005, d=0.25, s=0.0, r=0.05):
    t = np.arange(n) / SR; e = np.ones(n)
    ai = int(a * SR); e[:ai] = np.linspace(0, 1, max(ai, 1))[:ai]
    di = int(d * SR); seg = slice(ai, min(n, ai + di))
    e[seg] = 1 - (1 - s) * np.linspace(0, 1, seg.stop - seg.start)
    e[ai + di:] = s
    ri = int(r * SR)
    if ri and n > ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e

def voice(kind, f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    if kind == "marimba":
        x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 30)
        return x * env(n, 0.002, 0.35, 0.0, 0.02) * 0.5
    if kind == "epiano":
        x = np.sin(2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 4))
        return x * env(n, 0.004, 0.9, 0.25, 0.15) * 0.42
    if kind == "pluck":
        x = np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + np.sin(2 * np.pi * f * t) * 0.6
        return x * env(n, 0.002, 0.18, 0.0, 0.02) * 0.32
    if kind == "soft_square":
        x = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 3, 5, 7))
        return x * env(n, 0.04, 0.4, 0.55, 0.3) * 0.10
    if kind == "warm_pad":
        x = sum(np.sin(2 * np.pi * f * (1 + dt) * t) for dt in (-0.004, 0, 0.004)) / 3
        return x * env(n, 0.5, 0.5, 0.8, 0.6) * 0.13
    if kind == "bass":
        x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 2 * t)
        return x * env(n, 0.005, 0.3, 0.5, 0.08) * 0.35
    raise ValueError(kind)

rng_noise = np.random.default_rng(1)
def drum(kind, dur=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    if kind == "kick":
        f = 110 * np.exp(-t * 18) + 45
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 0.55
    if kind == "hat":
        x = rng_noise.standard_normal(n); x = np.diff(x, prepend=0)  # brighter
        return x * np.exp(-t * 60) * 0.07
    if kind == "click":  # a wooden ball click
        x = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120) + rng_noise.standard_normal(n) * np.exp(-t * 200) * 0.3
        return x * 0.16
    if kind == "snap":
        x = rng_noise.standard_normal(n) * np.exp(-t * 35)
        return x * 0.12
    if kind == "step":  # soft footstep
        f = 160 * np.exp(-t * 25) + 70
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22) * 0.25
    raise ValueError(kind)

PATTERNS = {  # 16 steps per bar
    "bouncy": {"kick": [0, 6, 8, 14], "click": [4, 12], "hat": [2, 6, 10, 14]},
    "walk": {"step": [0, 4, 8, 12], "hat": [2, 6, 10, 14], "snap": [12]},
    "lofi": {"kick": [0, 7, 10], "snap": [4, 12], "hat": [0, 2, 4, 6, 8, 10, 12, 14]},
    "four": {"kick": [0, 4, 8, 12], "snap": [4, 12], "hat": [2, 6, 10, 14]},
}

def render(name, seconds=40, seed=7):
    P = PRESETS[name]; rng = np.random.default_rng(seed)
    step = 60 / P["bpm"] / 4; bar = step * 16
    out = np.zeros(int((seconds + 2) * SR))
    def put(x, at):
        i = int(at * SR); j = min(len(out), i + len(x))
        if i < len(out): out[i:j] += x[: j - i]
    sc = SCALES[P["scale"]]; root = P["root"]
    def deg(d, octv=0): return root + 12 * (d // len(sc) + octv) + sc[d % len(sc)]
    # a 2-bar motif, repeated with small changes, so it feels like a tune and not random notes
    motif = [(s, int(rng.integers(0, len(sc) + 3))) for s in range(0, 32, 2) if rng.random() < P["lead_density"]]
    nbars = int(seconds / bar) + 1
    for b in range(nbars):
        t0 = b * bar; ch = P["prog"][b % len(P["prog"])]
        for s in CHORD_STEPS[P["scale"]]:
            put(voice(P["pad"], hz(deg(ch + s)), bar), t0)
        put(voice("bass", hz(deg(ch, -1)), step * 6), t0); put(voice("bass", hz(deg(ch, -1)), step * 4), t0 + step * 8)
        for inst, steps in PATTERNS[P["drums"]].items():
            if b == 0 and inst != "hat": continue  # soft start
            for s in steps:
                sw = P["swing"] * step if s % 4 == 2 else 0
                put(drum(inst), t0 + s * step + sw)
        if b >= 1:  # lead comes in on bar 2
            half = (b % 2) * 16
            for s, d in motif:
                if half <= s < half + 16:
                    var = 1 if (b // 4) % 2 and rng.random() < 0.25 else 0
                    put(voice(P["lead"], hz(deg(ch + d + var) + P["octave"] - 12 * (1 if d > len(sc) + 1 else 0)), step * 2.2), t0 + (s - half) * step)
    out = out[: int(seconds * SR)]
    fade = int(1.5 * SR); out[-fade:] *= np.linspace(1, 0, fade); out[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    out /= max(1e-6, np.max(np.abs(out))) / 0.8
    return out

if __name__ == "__main__":
    name, path = sys.argv[1], sys.argv[2]
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 40; seed = int(sys.argv[4]) if len(sys.argv) > 4 else 7
    x = render(name, secs, seed)
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "x.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-af", "loudnorm=I=-20:TP=-2:LRA=11", "-ar", "44100", "-ac", "2",
                        "-c:a", "aac", "-b:a", "160k", path], check=True)
    print(path)
