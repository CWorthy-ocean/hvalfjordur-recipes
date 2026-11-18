"""Make a temperature/salinity-only copy of a ROMS river forcing file.

A physics-only build (no MARBL) reads exactly two river tracers, temperature and
salinity. Forge stages a custom river file as it is, so the BGC tracers of the
Iceland2 custom river file have to be dropped before it can be used in
Iceland2_physics_10min_velocity.forge_blueprint.yaml.

The script keeps the first two tracers after checking that they are temp and salt.
If a forge blueprint is given, it also points the blueprint's river custom_file at
the new file and records the new file's content hash.

usage:
    python make_river_ts_only.py SRC.nc DST.nc [FORGE_BLUEPRINT.yaml]

On Anvil (the copy only has to exist while forge runs; forge stages its own copy):
    python make_river_ts_only.py \
        /anvil/projects/x-ees250129/x-uheede/INPUT_files/Iceland2_MARBL_2024/RT_EMOD/Iceland2_river_combied.nc \
        /anvil/scratch/x-uheede/iceland2_10min_velocity/Iceland2_river_combied_TS.nc \
        Iceland2_physics_10min_velocity.forge_blueprint.yaml
"""

import os
import sys

import xarray as xr


def tracer_names(ds):
    """Tracer names as a list of strings, or None if the file has no tracer_name."""
    if "tracer_name" not in ds:
        return None
    values = ds["tracer_name"].values
    if values.dtype.kind == "S" and values.ndim == 2:  # undecoded char array
        return [b"".join(row).decode().strip() for row in values]
    return [v.decode().strip() if isinstance(v, bytes) else str(v).strip() for v in values.ravel()]


def content_hash(path):
    """The hash forge records for a user-provided file, or None if unavailable."""
    try:
        from cstar.applications.forge.user_files import hash_netcdf_contents
    except ImportError:
        return None
    return hash_netcdf_contents(path)


def point_blueprint_at(blueprint, src, dst, new_hash):
    """Replace the river custom_file location (and its content_hash) in a forge blueprint."""
    lines = open(blueprint).read().splitlines(keepends=True)
    hits = [i for i, line in enumerate(lines) if line.strip() == f"location: {src}"]
    if len(hits) != 1:
        sys.exit(f"{blueprint}: expected exactly one 'location: {src}' line, found {len(hits)}")
    i = hits[0]
    lines[i] = lines[i].replace(src, dst)
    if new_hash and i + 1 < len(lines) and lines[i + 1].strip().startswith("content_hash:"):
        indent = lines[i + 1][: len(lines[i + 1]) - len(lines[i + 1].lstrip())]
        lines[i + 1] = f"{indent}content_hash: {new_hash}\n"
    open(blueprint, "w").write("".join(lines))


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    blueprint = sys.argv[3] if len(sys.argv) == 4 else None
    if os.path.exists(dst):
        sys.exit(f"{dst} already exists; remove it first")
    dst_dir = os.path.dirname(os.path.abspath(dst))
    if not os.access(dst_dir, os.W_OK):
        sys.exit(f"cannot write to {dst_dir}; choose a destination in a folder you can write to")

    with xr.open_dataset(src, decode_times=False, decode_timedelta=False) as ds:
        if "ntracers" not in ds.sizes:
            sys.exit(f"{src} has no 'ntracers' dimension")
        names = tracer_names(ds)
        print(f"{src}: {ds.sizes['ntracers']} tracers, first ones: {names[:4] if names else 'unnamed'}")
        if names is None:
            print("WARNING: no tracer_name variable; assuming the roms-tools order (temp, salt first)")
        elif [n.lower()[:4] for n in names[:2]] != ["temp", "salt"]:
            sys.exit("the first two tracers are not temp and salt; not writing anything")
        ds.isel(ntracers=slice(0, 2)).to_netcdf(dst)

    with xr.open_dataset(dst, decode_times=False, decode_timedelta=False) as out:
        print(f"wrote {dst}: {out.sizes['ntracers']} tracers {tracer_names(out) or ''}")

    new_hash = content_hash(dst)
    print(f"content hash: {new_hash or 'not computed (cstar not importable); forge will only warn'}")
    if blueprint:
        point_blueprint_at(blueprint, src, dst, new_hash)
        print(f"updated {blueprint}: river custom_file -> {dst}")


if __name__ == "__main__":
    main()
