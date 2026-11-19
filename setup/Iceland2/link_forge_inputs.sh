#!/bin/bash
# Hard-link the inputs of the Iceland2 custom-river forge run into the
# Iceland2_glodap_woa forge working directory, under the new blueprint's file names.
# Forge then reuses the grid, surface (ERA5, UNIFIED, MBL_co2), restoring (WOA) and
# tidal (TPXO) files instead of regenerating them. Both blueprints have the same grid,
# run window and forcing settings, so the files are the ones forge would make.
#
# The river file is not linked: forge stages the new one from the blueprint's custom_file.
# Hard links take no extra space; deleting either name leaves the other intact.
# Do not run forge with --clobber on the new blueprint.
#
# usage: bash link_forge_inputs.sh          # dry run: lists what it would link
#        bash link_forge_inputs.sh --link
set -euo pipefail

OLD_NAME=Iceland2_NEW_customriver_Iceland2_NEW_256procs
NEW_NAME=Iceland2_glodap_woa
ROOT=${ROOT:-/anvil/scratch/x-uheede/cstar/_forge_bp_runs}
OLD="$ROOT/$OLD_NAME/input_data"
NEW="$ROOT/$NEW_NAME/input_data"

DO=0
[ "${1:-}" = "--link" ] && DO=1
[ -d "$OLD" ] || { echo "no such folder: $OLD"; exit 1; }
[ "$DO" = 1 ] && mkdir -p "$NEW"

n=0
for f in "$OLD"/"$OLD_NAME"_*.nc; do
    base=$(basename "$f")
    suffix=${base#"${OLD_NAME}"_}
    case "$suffix" in
        river*) echo "skip    $base (forge stages the new river file)"; continue ;;
        *_nc4*) echo "skip    $base (unfinished intermediate)"; continue ;;
    esac
    target="$NEW/${NEW_NAME}_${suffix}"
    if [ -e "$target" ]; then
        echo "exists  $(basename "$target")"
        continue
    fi
    echo "link    $base -> $(basename "$target")"
    [ "$DO" = 1 ] && ln "$f" "$target"
    n=$((n + 1))
done

others=$(cd "$OLD" && ls | grep -v "^${OLD_NAME}_" || true)
[ -n "$others" ] && printf 'not linked (other names):\n%s\n' "$others"

if [ "$DO" = 1 ]; then
    echo "linked $n files into $NEW"
else
    echo "dry run: $n files to link; run again with --link"
fi
