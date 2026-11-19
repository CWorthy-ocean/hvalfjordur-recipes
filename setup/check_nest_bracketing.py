"""Check that each nest-from step's child boundary files cover its run.

For every workplan step with a `nest-from: path:` directive, this reads the time
records of all boundary files (`*bry*.nc`) in the listed folders, which is what
C-Star hands ROMS, and reports:
  - the last record at or before the step's start_date (needed);
  - the first record at or after the step's end_date (needed);
  - duplicate file names across the folders (C-Star cannot stage those);
  - duplicate record times across files.

Times are read from the first variable named in TIME_VARS, decoded with its
`units` attribute ("<unit> since <date>"), or else as seconds since --epoch.

Usage: python check_nest_bracketing.py WORKPLAN.yaml [--epoch 2000-01-01]
Exit status 1 if any step is not bracketed or has colliding file names.
"""
import argparse
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import netCDF4
import yaml

TIME_VARS = ("bry_time", "ocean_time", "time")
UNIT_SECONDS = {"second": 1, "seconds": 1, "minute": 60, "minutes": 60,
                "hour": 3600, "hours": 3600, "day": 86400, "days": 86400}

p = argparse.ArgumentParser()
p.add_argument("workplan", type=Path)
p.add_argument("--epoch", default="2000-01-01")
p.add_argument("--pattern", default="*bry*.nc")
a = p.parse_args()
default_epoch = datetime.fromisoformat(a.epoch)


UNIT_SECONDS_NAME = {1: "seconds", 60: "minutes", 3600: "hours", 86400: "days"}
REPORTED: set = set()


def parse_date(s: str) -> datetime:
    s = s.strip().replace("T", " ").replace("/", "-")[:19]
    return datetime.fromisoformat(s)


def record_times(f: Path) -> list[datetime]:
    with netCDF4.Dataset(f) as nc:
        name = next((v for v in TIME_VARS if v in nc.variables), None)
        if name is None:
            raise SystemExit(f"{f}: no time variable among {TIME_VARS}")
        var = nc.variables[name]
        units = getattr(var, "units", "").strip()
        long_name = getattr(var, "long_name", "")
        scale, epoch = 1, default_epoch
        m = re.match(r"(\w+)\s+since\s+(.+)", units)
        if m and m.group(1).lower() in UNIT_SECONDS:  # CF: "days since 2000-01-01"
            scale = UNIT_SECONDS[m.group(1).lower()]
            epoch = parse_date(m.group(2))
        elif units.lower() in UNIT_SECONDS:  # ROMS: units = "days", origin in long_name
            scale = UNIT_SECONDS[units.lower()]
            if mo := re.search(r"since\s+(\d{4}[-/]\d{2}[-/]\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?)",
                               long_name):
                epoch = parse_date(mo.group(1))
        decoding = (name, units, long_name, scale, epoch)
        if not REPORTED:
            print(f"time: {name} units={units!r} long_name={long_name!r} "
                  f"-> read as {UNIT_SECONDS_NAME.get(scale, scale)} since {epoch}")
        if decoding not in REPORTED and REPORTED:
            print(f"   note: {f.name} uses a different time encoding: {decoding}")
        REPORTED.add(decoding)
        # nearest second: a record meant for 00:00 stored in days can be a hair off
        return [epoch + timedelta(seconds=round(float(v) * scale)) for v in var[:]]


wp = yaml.safe_load(a.workplan.read_text())
ok = True
for step in wp["steps"]:
    nest = (step.get("directives") or {}).get("nest-from")
    if not nest or "path" not in nest:
        continue
    rp = step["blueprint_overrides"]["runtime_params"]
    start = datetime.fromisoformat(str(rp["start_date"]))
    end = datetime.fromisoformat(str(rp["end_date"]))
    dirs = [Path(s.strip()) for s in nest["path"].split(";") if s.strip()]

    print(f"\n== {step['name']}: {start} -> {end}")
    for d in dirs:
        n = len(list(d.glob(a.pattern))) if d.is_dir() else None
        if not n:
            ok = False
            print(f"   FAIL {'no such folder' if n is None else 'no ' + a.pattern + ' files in'}: {d}")
    files = [f for d in dirs for f in sorted(d.glob(a.pattern))]
    names = Counter(f.name for f in files)
    times = sorted((t, f) for f in files for t in record_times(f))
    before = [x for x in times if x[0] <= start]
    after = [x for x in times if x[0] >= end]
    dup_t = [t for t, n in Counter(t for t, _ in times).items() if n > 1]

    print(f"   {len(files)} files, {len(times)} records, "
          f"{times[0][0] if times else '-'} .. {times[-1][0] if times else '-'}")
    if before:
        t, f = before[-1]
        print(f"   OK   last record <= start: {t}  ({f.parent.parent.name}/{f.name})")
    else:
        ok = False
        print("   FAIL no record at or before start")
    if after:
        t, f = after[0]
        print(f"   OK   first record >= end : {t}  ({f.parent.parent.name}/{f.name})")
    else:
        ok = False
        print("   FAIL no record at or after end")
    if clash := [n for n, c in names.items() if c > 1]:
        ok = False
        print(f"   FAIL file names in more than one folder: {clash}")
    # two names (links) that resolve to the same file on disk
    targets = Counter(f.resolve() for f in files)
    if same := [t for t, c in targets.items() if c > 1]:
        ok = False
        print(f"   FAIL {len(same)} file(s) reached through more than one name, e.g. {same[0]}")
    else:
        print(f"   OK   no two names point to the same file")
    # same record time in more than one file (also catches copied files)
    if dup_t:
        ok = False
        print(f"   FAIL {len(dup_t)} record time(s) appear in more than one file, "
              f"e.g. {dup_t[0]}: "
              + ", ".join(f.name for t, f in times if t == dup_t[0]))
    else:
        print(f"   OK   no record time appears twice")
    # ROMS reads the files in list order (C-Star lists them by name) and only
    # searches forward, so name order must also be time order
    by_file = {}
    for t, f in times:
        by_file.setdefault(f, []).append(t)
    named = sorted(by_file, key=lambda f: (f.parent.as_posix(), f.name))
    out_of_order = [(a2, b) for a2, b in zip(named, named[1:])
                    if min(by_file[b]) < max(by_file[a2])]
    if out_of_order:
        ok = False
        a2, b = out_of_order[0]
        print(f"   FAIL {len(out_of_order)} file(s) out of time order by name, e.g. "
              f"{b.name} starts before {a2.name} ends")
    else:
        print("   OK   files in time order by name")
    # gaps: spacing between consecutive records over the span this step reads
    if before and after:
        span = sorted({t for t, _ in times if before[-1][0] <= t <= after[0][0]})
        steps = [(b - a2, a2) for a2, b in zip(span, span[1:])]
        if steps:
            typical = sorted(d for d, _ in steps)[len(steps) // 2]
            gaps = [(d, t) for d, t in steps if d > 1.5 * typical]
            if gaps:
                ok = False
                d, t = max(gaps)
                print(f"   FAIL {len(gaps)} gap(s) longer than 1.5 x the usual {typical} "
                      f"spacing; largest {d} after {t}")
            else:
                print(f"   OK   no gaps: records every {typical}")

raise SystemExit(0 if ok else 1)
