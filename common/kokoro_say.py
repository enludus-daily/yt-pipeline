"""Cute English narration with Kokoro (voice af_bella by default).
usage: python common/kokoro_say.py <voice> <speed> <out.wav> "<text>"
Model files: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 → .cache/kokoro/
"""
import os, sys, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro(os.environ.get("KOKORO_MODEL", ".cache/kokoro/kokoro-v1.0.onnx"), os.environ.get("KOKORO_VOICES", ".cache/kokoro/voices-v1.0.bin"))
voice, speed, out, text = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
samples, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
sf.write(out, samples, sr); print(out, round(len(samples)/sr, 2))
