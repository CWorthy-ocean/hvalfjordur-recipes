"""Gather a parent run's child boundary files for a nested workplan.

Step 1, merge: every *child_bry*.nc file of the source folders goes into MERGED_DIR,
which then holds the parent's whole boundary record in chronological order (the time
stamp in the file names). Unique names are symlinked. A name written by two
consecutive parent steps (each holds part of that file period) is concatenated along
the record dimension, sorted by time with duplicate times dropped, and written in the
original on-disk format (CDF5 for PIO), as merge_cdrgas_dirs.py does.

Step 2, split: every step of WORKPLAN whose nest-from path is a folder other than
MERGED_DIR gets that folder filled with symlinks to the merged files that cover the
step's start_date to end_date, plus MARGIN_DAYS either side. ROMS interpolates the
boundary values in time, so a step needs the records just before its start_date and
just after its end_date. The margin adds the files named up to MARGIN_DAYS before the
start, and one more file before those, whatever the file length. It also adds the files
named up to MARGIN_DAYS after the end. So neighbouring steps share their files around
the date where one ends and the next starts; each step's folder links them separately.
check_nest_bracketing.py then reads the records and confirms each step is covered.

Why split: C-Star hands ROMS every boundary file in a nest-from folder, in name order.
The ucla-roms build used for Iceland2 (constant_Fe, max_frc_files = 1000) reads at most
1000 forcing files and silently ignores the rest. Iceland1 writes a child_bry file every
12 hours, so Feb 2023 to Dec 2024 is about 1400 files, and a 6-month step about 370.

usage:
    python gather_child_bry.py WORKPLAN.yaml MERGED_DIR SRC_DIR [SRC_DIR ...] [--dry-run]

Run it again after a failed or partial attempt: links are replaced, merged files are
rewritten. It refuses to touch a split folder that holds anything but symlinks.
"""
import argparse
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import netCDF4
import numpy as np
import xarray as xr
import yaml

PATTERN = "*child_bry*.nc"
TIMESTAMP = re.compile(r"\.(\d{14})\.nc$")
MARGIN_DAYS = 1
MAX_FRC_FILES = 1000
TIME_VARS = ("bry_time", "ocean_time", "time")


def timestamp(path):
    m = TIMESTAMP.search(path.name)
    if m is None:
        raise SystemExit(f"{path}: no YYYYMMDDhhmmss time stamp in the name")
    return datetime.strptime(m.group(1), "%Y%m%d%H%M%S")


def parse_date(value):
    return datetime.fromisoformat(str(value).strip().replace("T", " ")[:19])


def merge(merged_dir, src_dirs, dry_run):
    by_name = defaultdict(list)
    for d in src_dirs:
        files = sorted(d.glob(PATTERN))
        if not files:
            raise SystemExit(f"no {PATTERN} files in {d}")
        for f in files:
            timestamp(f)  # every file must carry a time stamp
            by_name[f.name].append(f.resolve())

    if not dry_run:
        merged_dir.mkdir(parents=True, exist_ok=True)

    n_link = n_merge = 0
    for name, srcs in sorted(by_name.items()):
        target = merged_dir / name
        if len(srcs) == 1:
            if not dry_run:
                target.unlink(missing_ok=True)
                target.symlink_to(srcs[0])
            n_link += 1
            continue

        with netCDF4.Dataset(srcs[0]) as nc:
            fmt = nc.data_model
            rec_dim = next(k for k, v in nc.dimensions.items() if v.isunlimited())
            time_var = next(v for v in TIME_VARS if v in nc.variables)
        dss = [xr.open_dataset(s, decode_times=False) for s in srcs]
        ds = xr.concat(dss, dim=rec_dim, data_vars="minimal", coords="minimal", compat="override")
        _, keep = np.unique(ds[time_var].values, return_index=True)  # sorted, first copy of each time
        ds = ds.isel({rec_dim: keep})
        print(f"merge: {name} from {len(srcs)} steps "
              f"({' + '.join(str(d.sizes[rec_dim]) for d in dss)} records) -> {ds.sizes[rec_dim]} records")
        if not dry_run:
            target.unlink(missing_ok=True)
            tmp = target.with_suffix(".tmp.nc")
            ds.load().to_netcdf(tmp, format=fmt, engine="netcdf4", unlimited_dims=[rec_dim])
            tmp.rename(target)
        for d in dss:
            d.close()
        n_merge += 1

    names = sorted(by_name, key=lambda n: timestamp(Path(n)))
    print(f"{merged_dir}: {n_link} linked, {n_merge} merged, "
          f"{timestamp(Path(names[0]))} to {timestamp(Path(names[-1]))}")
    gaps = np.diff([timestamp(Path(n)).timestamp() for n in names])
    if len(gaps) and gaps.max() > 1.5 * np.median(gaps):
        i = int(gaps.argmax())
        print(f"WARNING: gap of {gaps.max() / 3600:.0f} h in the file names after {names[i]} "
              f"(files are normally {np.median(gaps) / 3600:.0f} h apart)")
    return names


def split(workplan, merged_dir, names, dry_run):
    wp = yaml.safe_load(workplan.read_text())
    stamps = [timestamp(Path(n)) for n in names]
    margin = timedelta(days=MARGIN_DAYS)
    for step in wp["steps"]:
        path = ((step.get("directives") or {}).get("nest-from") or {}).get("path")
        if not path or ";" in path:
            continue
        folder = Path(path)
        if folder.resolve() == merged_dir.resolve():
            print(f"{step['name']}: reads all of {merged_dir} ({len(names)} files)")
            continue
        params = (step.get("blueprint_overrides") or {}).get("runtime_params") or {}
        if "start_date" not in params or "end_date" not in params:
            raise SystemExit(f"step {step['name']}: set start_date and end_date in runtime_params")
        start, end = parse_date(params["start_date"]), parse_date(params["end_date"])
        chosen = [n for n, t in zip(names, stamps) if start - margin <= t <= end + margin]
        # the file before the window holds the records just before start_date
        first = names.index(chosen[0]) if chosen else 0
        if first > 0:
            chosen.insert(0, names[first - 1])
        if not chosen:
            raise SystemExit(f"step {step['name']}: no files between {start} and {end}")
        flag = "  WARNING: more files than max_frc_files" if len(chosen) > MAX_FRC_FILES - 50 else ""
        print(f"{step['name']}: {len(chosen)} files, {chosen[0]} .. {chosen[-1]} -> {folder}{flag}")
        n_before = sum(timestamp(Path(n)) < start for n in chosen)
        n_after = sum(timestamp(Path(n)) > end for n in chosen)
        print(f"    {n_before} files start before {start}, {n_after} start after {end}")
        if n_before == 0:
            print(f"    WARNING: no file starts before {start}; the parent output may begin too late")
        if n_after == 0:
            print(f"    WARNING: no file starts after {end}; check_nest_bracketing.py shows "
                  "whether the last file reaches it")
        if dry_run:
            continue
        if folder.exists():
            others = [p for p in folder.iterdir() if not p.is_symlink()]
            if others:
                raise SystemExit(f"{folder} holds files that are not symlinks ({others[0].name}); not touching it")
            for p in folder.iterdir():
                p.unlink()
        folder.mkdir(parents=True, exist_ok=True)
        for n in chosen:
            (folder / n).symlink_to((merged_dir / n).resolve())  # absolute: the original, or the merged file


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("workplan", type=Path)
    p.add_argument("merged_dir", type=Path)
    p.add_argument("src_dirs", type=Path, nargs="+")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    names = merge(a.merged_dir, a.src_dirs, a.dry_run)
    split(a.workplan, a.merged_dir, names, a.dry_run)


if __name__ == "__main__":
    main()
