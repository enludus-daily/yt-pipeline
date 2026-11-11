"""Per-app background music, synthesized from scratch (no samples, so no licensing questions).

Every app gets its OWN track. Tracks used to sound alike (same instruments, same groove), so a track is now
built from a GENRE (instruments, groove, harmony, song form) plus a per-app seed, and a new app must not reuse
the genre of the most recent apps (checked against apps/*/bgm.json).

usage:
  python common/bgm.py new <app> [--genre G] [--seconds 40]   # pick an unused genre, write apps/<app>/bgm.m4a + bgm.json
  python common/bgm.py render <genre> <out.m4a> [--seed N] [--seconds 40] [--bpm B] [--key K]
  python common/bgm.py list                                    # genres, and which apps used which

genres: lofi, chiptune, bossa, synthwave, folk, ambient, funk, waltz, marimba_pop, city_walk
(marimba_pop = Tamahebi 2026-11-11, city_walk = Umeda 2026-11-11)
"""
import argparse, glob, hashlib, json, os, subprocess, sys, tempfile, wave
import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTE = {"C": 60, "C#": 61, "D": 62, "Eb": 63, "E": 64, "F": 65, "F#": 66, "G": 67, "Ab": 68, "A": 69, "Bb": 70, "B": 71}
SCALES = {"major": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10], "dorian": [0, 2, 3, 5, 7, 9, 10],
          "mixolydian": [0, 2, 4, 5, 7, 9, 10], "major_pent": [0, 2, 4, 7, 9], "minor_pent": [0, 3, 5, 7, 10]}

# Each genre: tempo range, meter, scales, progressions (scale degrees), chord size, instruments, groove, form
GENRES = {
    "lofi":       dict(bpm=(72, 86), meter=4, scales=["dorian", "minor"], progs=[[0, 3, 6, 2], [1, 4, 0, 5], [0, 5, 3, 4]], sevenths=True,
                       lead="rhodes", comp="rhodes_chord", bass="sub", drums="lofi", swing=0.22, density=0.35, extras=["crackle"]),
    "chiptune":   dict(bpm=(140, 160), meter=4, scales=["major", "minor"], progs=[[0, 5, 3, 4], [0, 3, 4, 4], [5, 3, 0, 4]], sevenths=False,
                       lead="square", comp="arp_pulse", bass="tri", drums="chip", swing=0.0, density=0.75, extras=[]),
    "bossa":      dict(bpm=(118, 132), meter=4, scales=["major", "dorian"], progs=[[1, 4, 0, 0], [0, 5, 1, 4], [3, 2, 1, 4]], sevenths=True,
                       lead="flute", comp="nylon_comp", bass="upright", drums="bossa", swing=0.0, density=0.4, extras=["shaker"]),
    "synthwave":  dict(bpm=(96, 112), meter=4, scales=["minor"], progs=[[0, 5, 2, 6], [0, 6, 5, 6], [5, 3, 0, 4]], sevenths=False,
                       lead="saw_lead", comp="saw_pad", bass="octave_saw", drums="gated", swing=0.0, density=0.45, extras=[]),
    "folk":       dict(bpm=(100, 116), meter=4, scales=["major", "mixolydian"], progs=[[0, 4, 5, 3], [0, 3, 0, 4], [5, 3, 0, 4]], sevenths=False,
                       lead="whistle", comp="strum", bass="pluck_bass", drums="folk", swing=0.08, density=0.45, extras=["claps"]),
    "ambient":    dict(bpm=(64, 76), meter=4, scales=["major_pent", "minor_pent"], progs=[[0, 3, 4, 3], [0, 5, 3, 4]], sevenths=True,
                       lead="bell", comp="slow_pad", bass="sub", drums="none", swing=0.0, density=0.18, extras=[]),
    "funk":       dict(bpm=(104, 116), meter=4, scales=["dorian", "mixolydian"], progs=[[0, 3, 0, 3], [0, 0, 3, 4]], sevenths=True,
                       lead="clav", comp="stab", bass="slap", drums="funk", swing=0.12, density=0.55, extras=[]),
    "waltz":      dict(bpm=(132, 150), meter=3, scales=["major", "minor"], progs=[[0, 3, 4, 0], [0, 5, 3, 4]], sevenths=False,
                       lead="music_box", comp="waltz_comp", bass="pluck_bass", drums="waltz", swing=0.0, density=0.5, extras=[]),
    "marimba_pop": dict(bpm=(116, 120), meter=4, scales=["major"], progs=[[0, 5, 3, 4]], sevenths=False,
                       lead="marimba", comp="soft_square", bass="sub", drums="bouncy", swing=0.12, density=0.62, extras=[]),
    "city_walk":  dict(bpm=(100, 104), meter=4, scales=["major_pent"], progs=[[0, 4, 5, 3]], sevenths=False,
                       lead="rhodes", comp="slow_pad", bass="sub", drums="walk", swing=0.0, density=0.45, extras=[]),
}
GROOVES = {  # steps per bar: 16 (4/4) or 12 (3/4)
    "lofi": {"kick": [0, 7, 10], "snare": [4, 12], "hat": [0, 2, 4, 6, 8, 10, 12, 14]},
    "chip": {"kick": [0, 8], "noise_snare": [4, 12], "hat": [2, 6, 10, 14]},
    "bossa": {"kick": [0, 6, 8, 14], "rim": [3, 6, 10, 13], "hat": [0, 2, 4, 6, 8, 10, 12, 14]},
    "gated": {"kick": [0, 4, 8, 12], "big_snare": [4, 12], "hat": [2, 6, 10, 14]},
    "folk": {"kick": [0, 8], "snare": [4, 12], "hat": [0, 4, 8, 12]},
    "none": {},
    "funk": {"kick": [0, 3, 10], "snare": [4, 12], "hat": list(range(16)), "ghost": [7, 9, 15]},
    "waltz": {"kick": [0], "rim": [4, 8], "hat": [2, 6, 10]},
    "bouncy": {"kick": [0, 6, 8, 14], "click": [4, 12], "hat": [2, 6, 10, 14]},
    "walk": {"step": [0, 4, 8, 12], "hat": [2, 6, 10, 14], "snap": [12]},
}

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def adsr(n, a, d, s, r):
    e = np.full(n, s, dtype=float); ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    ai = min(ai, n); e[:ai] = np.linspace(0, 1, max(ai, 1))[:ai]
    dj = min(n, ai + di); e[ai:dj] = np.linspace(1, s, max(dj - ai, 1))[: dj - ai]
    if ri and n > ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e
def lp(x, a):  # one-pole low-pass, a in (0,1): smaller = darker
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a * (x[i] - acc); y[i] = acc
    return y

def inst(kind, f, dur, rng):
    n = max(1, int(dur * SR)); t = np.arange(n) / SR; ph = 2 * np.pi * f * t
    saw = lambda: 2 * ((f * t) % 1) - 1
    if kind == "rhodes":  return np.sin(ph + 0.5 * np.sin(2 * ph) * np.exp(-t * 3)) * adsr(n, .005, 1.2, .2, .2) * .38
    if kind == "rhodes_chord": return inst("rhodes", f, dur, rng) * .6
    if kind == "square":  return np.sign(np.sin(ph)) * adsr(n, .002, .12, .5, .03) * .13
    if kind == "arp_pulse": return ((np.sin(ph) > .5).astype(float) - .3) * adsr(n, .001, .08, .2, .02) * .12
    if kind == "tri":     return (2 * np.abs(saw()) - 1) * adsr(n, .003, .2, .7, .05) * .4
    if kind == "flute":   return (np.sin(ph) + .15 * np.sin(2 * ph) + .02 * rng.standard_normal(n)) * adsr(n, .06, .3, .7, .15) * (1 + .03 * np.sin(2 * np.pi * 5 * t)) * .25
    if kind == "nylon_comp": return (np.sin(ph) + .4 * np.sin(2 * ph) * np.exp(-t * 6)) * adsr(n, .003, .5, 0, .05) * .25
    if kind == "upright": return np.sin(ph) * adsr(n, .01, .45, .2, .08) * .45
    if kind == "saw_lead": return lp(saw() * adsr(n, .01, .3, .6, .1), .25) * .22
    if kind == "saw_pad":  return lp(sum(2 * ((f * (1 + d) * t) % 1) - 1 for d in (-.006, 0, .006)) / 3, .08) * adsr(n, .4, .5, .8, .5) * .2
    if kind == "octave_saw": return lp(saw(), .15) * adsr(n, .005, .15, .6, .04) * .35
    if kind == "whistle": return np.sin(ph + .2 * np.sin(2 * np.pi * 6 * t)) * adsr(n, .05, .2, .6, .1) * .22
    if kind == "strum":   return (np.sin(ph) + .5 * np.sin(2 * ph) + .25 * np.sin(3 * ph)) * np.exp(-t * 4) * adsr(n, .004, 1, 1, .05) * .14
    if kind == "pluck_bass": return (np.sin(ph) + .3 * np.sin(2 * ph)) * adsr(n, .004, .3, .3, .05) * .4
    if kind == "bell":    return (np.sin(ph) + .4 * np.sin(2.76 * ph) * np.exp(-t * 2)) * adsr(n, .005, 2.5, 0, .3) * .25
    if kind == "slow_pad": return sum(np.sin(2 * np.pi * f * (1 + d) * t) for d in (-.004, 0, .004)) / 3 * adsr(n, .8, .5, .85, .8) * .14
    if kind == "clav":    return lp(np.sign(np.sin(ph)) * .6 + saw() * .4, .4) * adsr(n, .001, .12, .0, .02) * .2
    if kind == "stab":    return lp(saw(), .3) * adsr(n, .002, .12, 0, .03) * .14
    if kind == "slap":    return (np.sin(ph) + .5 * np.sin(2 * ph) * np.exp(-t * 20)) * adsr(n, .002, .2, .4, .04) * .45
    if kind == "music_box": return (np.sin(ph) + .3 * np.sin(4 * ph) * np.exp(-t * 8)) * adsr(n, .002, 1.2, 0, .1) * .25
    if kind == "waltz_comp": return inst("rhodes", f, dur, rng) * .5
    if kind == "marimba": return (np.sin(ph) + .35 * np.sin(4 * ph) * np.exp(-t * 30)) * adsr(n, .002, .35, 0, .02) * .5
    if kind == "soft_square": return sum(np.sin(k * ph) / k for k in (1, 3, 5, 7)) * adsr(n, .04, .4, .55, .3) * .1
    if kind == "sub":     return (np.sin(ph) + .25 * np.sin(2 * ph)) * adsr(n, .005, .3, .5, .08) * .35
    raise ValueError(kind)

def drum(kind, rng):
    n = int(.3 * SR); t = np.arange(n) / SR; noise = rng.standard_normal(n)
    sweep = lambda a, b, k: np.sin(2 * np.pi * np.cumsum(a * np.exp(-t * k) + b) / SR)
    if kind == "kick": return sweep(110, 45, 18) * np.exp(-t * 9) * .55
    if kind == "snare": return (noise * .6 + sweep(180, 0, 30) * .4) * np.exp(-t * 22) * .22
    if kind == "big_snare": return lp(noise, .5) * np.exp(-t * 8) * .3
    if kind == "noise_snare": return np.sign(noise) * np.exp(-t * 28) * .12
    if kind == "hat": return np.diff(noise, prepend=0) * np.exp(-t * 60) * .06
    if kind == "rim": return np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 90) * .14
    if kind == "ghost": return noise * np.exp(-t * 40) * .06
    if kind == "click": return (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120) + noise * np.exp(-t * 200) * .3) * .16
    if kind == "snap": return noise * np.exp(-t * 35) * .12
    if kind == "step": return sweep(160, 70, 25) * np.exp(-t * 22) * .25
    raise ValueError(kind)

def render(genre, seconds=40.0, seed=7, bpm=None, key=None):
    G = GENRES[genre]; rng = np.random.default_rng(seed)
    bpm = bpm or int(rng.integers(G["bpm"][0], G["bpm"][1] + 1))
    root = NOTE[key] if key else int(rng.integers(55, 66))
    scale = SCALES[G["scales"][int(rng.integers(len(G["scales"])))]]
    prog = G["progs"][int(rng.integers(len(G["progs"])))]
    meter = G["meter"]; steps = 4 * meter; step = 60 / bpm / 4; bar = step * steps
    out = np.zeros(int((seconds + 3) * SR))
    def put(x, at, gain=1.0):
        i = int(at * SR); j = min(len(out), i + len(x))
        if 0 <= i < len(out): out[i:j] += x[: j - i] * gain
    def deg(d, octv=0): return root + 12 * (d // len(scale) + octv) + scale[d % len(scale)]
    chord_tones = [0, 2, 4, 6] if G["sevenths"] else [0, 2, 4]
    # song form: intro (pad only) / A / B (lead up an octave, busier) / A / outro
    nbars = int(seconds / bar) + 1
    form = ["intro"] + ["A"] * 4 + ["B"] * 4 + ["A"] * 4 + ["B"] * 4
    motifA = [(s, int(rng.integers(0, len(scale) + 2))) for s in range(0, 2 * steps, 2) if rng.random() < G["density"]]
    motifB = [(s, int(rng.integers(2, len(scale) + 4))) for s in range(0, 2 * steps) if rng.random() < G["density"] * .7]
    for b in range(nbars):
        part = form[min(b, len(form) - 1)] if b < nbars - 1 else "outro"
        t0 = b * bar; ch = prog[b % len(prog)]
        for k in chord_tones:  # comp / pad
            if G["comp"] in ("nylon_comp", "stab", "strum", "waltz_comp", "arp_pulse"):
                hits = {"nylon_comp": [0, 3, 6, 10, 12], "stab": [2, 6, 10, 14], "strum": [0, 4, 6, 8, 12, 14], "waltz_comp": [4, 8], "arp_pulse": list(range(0, steps, 2))}[G["comp"]]
                for i, s in enumerate(hits):
                    if s < steps:
                        tone = chord_tones[i % len(chord_tones)] if G["comp"] == "arp_pulse" else k
                        if G["comp"] != "arp_pulse" or k == 0:
                            put(inst(G["comp"], hz(deg(ch + tone)), step * 2, rng), t0 + s * step + (0.012 * k if G["comp"] == "strum" else 0))
            else:
                put(inst(G["comp"], hz(deg(ch + k)), bar, rng), t0)
        if part != "intro":
            for s in ([0, steps // 2] if meter == 4 else [0]):  # bass
                put(inst(G["bass"], hz(deg(ch, -1)), step * (6 if meter == 4 else 10), rng), t0 + s * step)
            for name, hits in GROOVES[G["drums"]].items():
                for s in hits:
                    if s < steps:
                        sw = G["swing"] * step if s % 4 == 2 else 0
                        put(drum(name, rng), t0 + s * step + sw, 0.6 if part == "outro" else 1.0)
            motif, octv = (motifA, 0) if part in ("A", "outro") else (motifB, 1)
            half = (b % 2) * steps
            for s, d in motif:
                if half <= s < half + steps:
                    put(inst(G["lead"], hz(deg(ch + d) + 12 * octv), step * 2.4, rng), t0 + (s - half) * step)
        if "crackle" in G["extras"]:
            put(rng.standard_normal(int(bar * SR)) * (rng.random(int(bar * SR)) > .9985) * .05, t0)
        if "shaker" in G["extras"] and part != "intro":
            for s in range(0, steps, 2): put(lp(rng.standard_normal(int(.08 * SR)), .6) * np.exp(-np.arange(int(.08 * SR)) / SR * 40) * .05, t0 + s * step)
        if "claps" in G["extras"] and part == "B":
            for s in (4, 12): put(drum("snap", rng) * 1.4, t0 + s * step)
    out = out[: int(seconds * SR)]
    f = int(1.5 * SR); out[-f:] *= np.linspace(1, 0, f); out[: int(.3 * SR)] *= np.linspace(0, 1, int(.3 * SR))
    out /= max(1e-6, np.max(np.abs(out))) / .8
    return out, dict(genre=genre, bpm=bpm, root=root, scale=[k for k, v in SCALES.items() if v == scale][0], progression=prog, seed=seed)

def write(x, path):
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "x.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-af", "loudnorm=I=-20:TP=-2:LRA=11", "-ar", "44100", "-ac", "2",
                        "-c:a", "aac", "-b:a", "160k", path], check=True)

def used():
    rows = []
    for f in glob.glob(os.path.join(ROOT, "apps", "*", "bgm.json")):
        d = json.load(open(f)); d["app"] = os.path.basename(os.path.dirname(f)); rows.append(d)
    return sorted(rows, key=lambda d: d.get("made", ""))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("new"); a.add_argument("app"); a.add_argument("--genre"); a.add_argument("--seconds", type=float, default=40)
    r = sub.add_parser("render"); r.add_argument("genre"); r.add_argument("out"); r.add_argument("--seed", type=int, default=7)
    r.add_argument("--seconds", type=float, default=40); r.add_argument("--bpm", type=int); r.add_argument("--key")
    sub.add_parser("list")
    o = ap.parse_args()
    if o.cmd == "list":
        print("genres:", ", ".join(GENRES)); [print(f"  {d['app']}: {d['genre']} {d['bpm']}bpm") for d in used()]
    elif o.cmd == "render":
        x, meta = render(o.genre, o.seconds, o.seed, o.bpm, o.key); write(x, o.out); print(o.out, meta)
    else:
        recent = [d["genre"] for d in used()][-5:]
        genre = o.genre or next(g for g in sorted(GENRES, key=lambda g: hashlib.sha1((o.app + g).encode()).hexdigest()) if g not in recent)
        if genre in recent and not o.genre:
            sys.exit("no unused genre")
        if genre in recent:
            print(f"warning: {genre} was used by one of the last 5 apps ({recent})")
        seed = int(hashlib.sha1(o.app.encode()).hexdigest()[:8], 16)
        x, meta = render(genre, o.seconds, seed)
        d = os.path.join(ROOT, "apps", o.app); os.makedirs(d, exist_ok=True)
        write(x, os.path.join(d, "bgm.m4a"))
        import datetime; meta["made"] = datetime.datetime.now().isoformat(timespec="seconds")
        json.dump(meta, open(os.path.join(d, "bgm.json"), "w"), indent=2); print(os.path.join(d, "bgm.m4a"), meta)
