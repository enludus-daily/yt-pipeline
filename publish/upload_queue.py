"""Upload every video in publish/queue/ (<name>.mp4 + <name>.json) with common/upload.py,
then move both files to publish/done/. Run on the computer that holds .cache/youtube-token.json.

usage: python publish/upload_queue.py [--dry-run]
"""
import glob, os, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q, DONE = os.path.join(ROOT, "publish", "queue"), os.path.join(ROOT, "publish", "done")
dry = "--dry-run" in sys.argv
os.makedirs(DONE, exist_ok=True)
for mp4 in sorted(glob.glob(os.path.join(Q, "*.mp4"))):
    meta = mp4[:-4] + ".json"
    if not os.path.exists(meta):
        print(f"skip (no metadata): {mp4}"); continue
    args = [sys.executable, os.path.join(ROOT, "common", "upload.py"), mp4, meta] + (["--dry-run"] if dry else [])
    print("$", " ".join(os.path.relpath(a, ROOT) if a.startswith(ROOT) else a for a in args[1:]))
    subprocess.run(args, check=True)
    if not dry:
        for f in (mp4, meta): shutil.move(f, os.path.join(DONE, os.path.basename(f)))
