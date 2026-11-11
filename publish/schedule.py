"""Give every queued video a publish time in the US daytime (not the middle of the night there).

usage: python publish/schedule.py [--start YYYY-MM-DD] [--dry-run]

Slots (US Eastern time, DST handled by zoneinfo):
  12:00 ET  "AI ships an app a day" (files named day<N>-*)   = 9:00 PT, 02:00 JST next day (winter)
  16:00 ET  everything else (app promos, word puzzles)       = 13:00 PT, 06:00 JST next day (winter)
One video per slot per day. Slots already used are read from publish/scheduled.json (kept in the repo).
Writes privacyStatus "private" + publishAt into each queued .json, so YouTube publishes it on time by itself.
"""
import argparse, datetime as dt, glob, json, os
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(ROOT, "publish", "queue"); LOG = os.path.join(ROOT, "publish", "scheduled.json")
ET = ZoneInfo("America/New_York")
SLOTS = {"daily": 12, "other": 16}

ap = argparse.ArgumentParser(); ap.add_argument("--start"); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
taken = json.load(open(LOG)) if os.path.exists(LOG) else {}
now = dt.datetime.now(ET)
start = dt.date.fromisoformat(a.start) if a.start else (now + dt.timedelta(hours=2)).date()

def next_slot(kind):
    day = start
    while True:
        t = dt.datetime.combine(day, dt.time(SLOTS[kind]), ET)
        key = t.isoformat()
        if t > now + dt.timedelta(minutes=30) and key not in taken.values():
            return t
        day += dt.timedelta(days=1)

# series first (by day number), then the rest by name
files = sorted(glob.glob(os.path.join(Q, "*.json")))
files.sort(key=lambda f: (0 if os.path.basename(f).startswith("day") else 1,
                          int(''.join(c for c in os.path.basename(f).split('-')[0] if c.isdigit()) or 0), f))
for f in files:
    name = os.path.basename(f)[:-5]
    if name in taken:
        print(f"{name}: already scheduled {taken[name]}"); continue
    t = next_slot("daily" if name.startswith("day") else "other")
    taken[name] = t.isoformat()
    meta = json.load(open(f)); meta["privacyStatus"] = "private"; meta["publishAt"] = t.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    jst = t.astimezone(ZoneInfo("Asia/Tokyo"))
    print(f"{name}: {t:%a %b %d %H:%M} ET  ({jst:%m/%d %H:%M} JST)")
    if not a.dry_run:
        json.dump(meta, open(f, "w"), ensure_ascii=False, indent=2); open(f, "a").write("\n")
if not a.dry_run:
    json.dump(taken, open(LOG, "w"), indent=2)
