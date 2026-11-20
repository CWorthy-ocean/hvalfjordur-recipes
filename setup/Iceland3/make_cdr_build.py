"""Copy the compile-time code of a ROMS run blueprint and switch on CDR_FORCING.

The November Iceland3 run (iceland3-nov2024) was built without CDR_FORCING. The OAE
members (wp_Iceland3_oae_ens4/5/6.yaml) reuse its run blueprint unchanged and point
`code.compile_time.location` at the folder this script writes: a copy of the run's
compile-time folder whose cppdefs.opt also defines CDR_FORCING. A workplan cannot
add a cppdef any other way; C-Star compiles whatever cppdefs.opt that folder holds.

The CDR output stream (CDR_OUTPUT_SETTINGS, the ALK_source fields) also needs MARBL
and MARBL_DIAGS; the script stops if either is missing.

usage:
    python make_cdr_build.py RUN_BLUEPRINT.yaml DEST_DIR [--dry-run]

It refuses to overwrite an existing DEST_DIR.
"""
import argparse
import difflib
import re
import shutil
import sys
from pathlib import Path

import yaml

MACRO = "CDR_FORCING"
REQUIRED = ("MARBL", "MARBL_DIAGS")


def defined(text, macro):
    # The same per-line test C-Star and the ROMS Makedefs use: an active #define
    return any(re.search(rf"^[^!]*#\s*define\s+{macro}\b", line) for line in text.splitlines())


def with_cdr_forcing(text):
    """cppdefs.opt text with CDR_FORCING defined: an #undef line is flipped, otherwise
    the #define goes on the line after #define MARBL."""
    if defined(text, MACRO):
        return text
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if re.match(rf"^\s*#\s*undef\s+{MACRO}\b", line):
            lines[i] = f"#define {MACRO}\n"
            return "".join(lines)
    for i, line in enumerate(lines):
        if re.match(r"^\s*#\s*define\s+MARBL\b(?!_)", line):
            lines[i + 1:i + 1] = ["! OAE members: CDR forcing and the CDR output stream (make_cdr_build.py)\n",
                                  f"#define {MACRO}\n"]
            return "".join(lines)
    raise SystemExit("no '#define MARBL' line to put CDR_FORCING after")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("blueprint", type=Path, help="the ROMS run blueprint (B_*.yaml) of the base run")
    p.add_argument("dest", type=Path, help="new compile-time folder")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    bp = yaml.safe_load(a.blueprint.read_text())
    compile_time = (bp.get("code") or {}).get("compile_time") or {}
    location = str(compile_time.get("location") or "")
    if not location:
        raise SystemExit(f"{a.blueprint}: no code.compile_time.location")
    if "://" in location:
        raise SystemExit(f"code.compile_time.location is {location}, not a local folder; "
                         "check out that repository and edit its cppdefs.opt by hand")
    # A workplan override replaces only `location`: the blueprint's filter (directory,
    # files) still applies to the new folder, so the copy keeps the same layout.
    filt = compile_time.get("filter") or {}
    subdir = filt.get("directory") or ""
    src_root = Path(location).expanduser()
    src = src_root / subdir
    if not (src / "cppdefs.opt").is_file():
        raise SystemExit(f"{src} has no cppdefs.opt")
    files = filt.get("files") or []
    print(f"compile-time code of {a.blueprint.name}: {src}" + (f" (files: {', '.join(files)})" if files else ""))
    for key in ("branch", "commit"):
        if compile_time.get(key) not in (None, "", "na"):
            print(f"note: code.compile_time.{key} is {compile_time[key]!r}; it still applies to the new folder")

    old = (src / "cppdefs.opt").read_text()
    if missing := [m for m in REQUIRED if not defined(old, m)]:
        raise SystemExit(f"{src / 'cppdefs.opt'} does not define {', '.join(missing)}; "
                         "the CDR output stream needs MARBL and MARBL_DIAGS")
    new = with_cdr_forcing(old)
    dest_file = a.dest / subdir / "cppdefs.opt"
    sys.stdout.writelines(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile=str(src / "cppdefs.opt"), tofile=str(dest_file)))
    if new == old:
        print(f"{MACRO} is already defined")

    if a.dry_run:
        return
    if a.dest.exists():
        raise SystemExit(f"{a.dest} exists; remove it or pick another folder")
    shutil.copytree(src_root, a.dest, symlinks=False)
    dest_file.write_text(new)
    print(f"wrote {a.dest}; set code.compile_time.location to {a.dest.resolve()}")


if __name__ == "__main__":
    main()
