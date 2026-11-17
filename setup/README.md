# Model setup

This folder holds everything needed to create and run the nested ROMS-MARBL simulations with [C-Star](https://github.com/CWorthy-ocean/C-Star):

- **Forge blueprints** (`*.forge_blueprint.yaml`) describe a domain: grid, time step, partitioning, forcing sources and code versions. `cstar forge` turns a blueprint into model inputs and a run blueprint.
- **Workplans** (`wp_*.yaml`) chain runs: spin-up and yearly segments, nesting a child domain in its parent (`nest_ic`, `nest-from`), and continuing from restarts.
- **Notebooks and scripts for steps forge does not do**, such as the custom river files, the passive-tracer setup and the OAE (CDR) release forcing. Their outputs are passed to the blueprints as custom files.

The roms-tools setup notebooks used for the initial submission (`setup_iceland0-3.ipynb`) are deprecated and kept in `archive/notebooks/setup/`.

> **Draft.** Not all blueprints and workplans are in place yet. The tables below list what each domain folder holds now and what still has to be added.

## Nesting chain

| Domain | Region | Grid | Δx | Δt | Simulated period | Parent |
|---|---|---|---|---|---|---|
| Iceland0 | North Atlantic around Iceland | 512 × 512 × 60, 1280 × 1280 km | 2.5 km | 180 s | 2023-01-01 – 2024-12-31 | GLORYS (open boundaries) |
| Iceland1 | First nest, southwest Iceland | 512 × 384 × 60, 384 × 288 km | 750 m | 60 s | 2023-01-02 – 2024-12-31 | Iceland0 |
| Iceland2 | Icelandic shelf and the approaches to Hvalfjörður | 512 × 512 × 60, 102.4 × 102.4 km | 200 m | 15 s | 2023-02-01 – 2024-12-31 | Iceland1 |
| Iceland3 | Hvalfjörður (fjord scale) | 640 × 384 × 60, 32 × 19.2 km | 50 m | 5 s | 2024-06-15 – 2024-11-30 | Iceland2 |

These are the values in each forge blueprint; workplan steps can override the dates and the time step. All domains use θs = 5, θb = 2, hc = 300 m, surface forcing from ERA5 and tides from TPXO (15 constituents).

## Contents by domain

Each domain folder is self-contained: its blueprint, its workplan(s), and any inputs prepared outside forge.

### `Iceland0/`

| File | Role | Status |
|---|---|---|
| `cson_roms-marbl_v0.1_Iceland0_256procs_180dt.forge_blueprint.yaml` | Forge blueprint: GLORYS initial and boundary conditions, ERA5, TPXO, GLOFAS rivers | present |
| `wp_Iceland0_glodap_woa.yaml` | Workplan: spin-up (2 weeks) → 2023 → 2024, with GLODAP/WOA BGC initial and boundary conditions | present |

### `Iceland1/`

| File | Role | Status |
|---|---|---|
| `Iceland1_256procs.forge_blueprint.yaml` | Forge blueprint nested in Iceland0 | present |
| `wp_Iceland1_glodap_woa.yaml` | Workplan: `nest_ic` from Iceland0 → spin-up → 2023 → 2024 | present |
| `merge_cdrgas_dirs.py` | Merges Iceland0's child-boundary output from consecutive steps into one folder (used by the workplan's `nest-from`) | to add |

### `Iceland2/`

| File | Role | Status |
|---|---|---|
| `Iceland2_NEW_customriver_Iceland2_NEW_256procs.forge_blueprint.yaml` | Forge blueprint nested in Iceland1, river forcing from a custom file | present |
| `Iceland2_river_forcing.ipynb` | Builds the custom Iceland2 river forcing file | present |
| `passive_tracer_setup.ipynb` | Adds a passive dye tracer to an Iceland2 run (initial and boundary files), the model analogue of the SF₆ release | present |
| `wp_Iceland2_*.yaml` | Workplan for the 2023–2024 run nested in Iceland1 | to add |
| `wp_Iceland2_dye.yaml` | Workplan for the passive-tracer run used in `analysis/sf6_model.ipynb` | to add |

### `Iceland3/`

| File | Role | Status |
|---|---|---|
| `Iceland3_256procs.forge_blueprint.yaml` | Forge blueprint nested in Iceland2, river forcing from a custom file, no CDR forcing (`cdr: none`) | present |
| `wp_Iceland3_corr.yaml` | Workplan: `nest_ic` from the corrected Iceland2 restart → November 2024 run | present |
| `CDR_forcing_creation.ipynb` | Builds the OAE (alkalinity release) forcing for the ensemble members CDR1–6 | present |
| `Iceland3_river_forcing.ipynb` | Builds the custom Iceland3 river forcing file. The code is still in `archive/notebooks/setup/setup_iceland3.ipynb` (river section). | to add |
| `correct_alk_dic.py` | Corrects the Iceland2 ALK/DIC inputs (f = 0.51, ρ = 1027) before nesting; referenced by `wp_Iceland3_corr.yaml` | to add |
| `wp_Iceland3_jul2024.yaml` | Workplan for the July 2024 run (the window of CDR1–3) | to add |
| `wp_Iceland3_oae.yaml` (or one per member) | OAE ensemble CDR1–6: the July or November base run with the CDR forcing file from `CDR_forcing_creation.ipynb` | to add |

## Order of operations

1. **Iceland0:** run `wp_Iceland0_glodap_woa.yaml`.
2. **Iceland1:** run `wp_Iceland1_glodap_woa.yaml`. Its `nest_ic` step interpolates the Iceland0 restart; its run steps read Iceland0's child boundary files.
3. **Iceland2:** run `Iceland2_river_forcing.ipynb`, forge the blueprint, then run the (to be added) Iceland2 workplan. For the dye run, run `passive_tracer_setup.ipynb` first.
4. **Iceland3:** build the river file, forge the blueprint, correct the Iceland2 ALK/DIC (`correct_alk_dic.py`), then run `wp_Iceland3_corr.yaml` (November) and the July workplan. For the OAE ensemble, run `CDR_forcing_creation.ipynb` and the ensemble workplan(s).
5. Post-processing and figures: see `analysis/` (for the OAE ensemble: `mixed_layer_depth.ipynb` → `OAE_ensemble.ipynb` → `oae_analysis.ipynb`).

## Conventions and open points

- **File names.** Blueprints are named after the forge run that produced them, which is why the names vary. A later clean-up could rename them to `Iceland{n}.forge_blueprint.yaml`; the `name:` and `working_dir:` fields inside would need the same change.
- **Paths.** Workplans currently point at absolute Anvil paths: the run blueprints forge generated (`.../blueprints/B_*.yaml`), restart files and child-boundary folders. They document what was run, but cannot be used elsewhere as they are. Deciding whether to point them at the blueprints in this folder (or to document the forge step that produces each `B_*.yaml`) is open.
- **Model code.** The Iceland2 and Iceland3 blueprints use the `constant_Fe` branch of ucla-roms; Iceland0 and Iceland1 use `main`. The Iceland1 workplan overrides ucla-roms to 0.13.1, because it needs more than 360 boundary files.
- The custom-forcing notebooks write NetCDF files whose paths go into the blueprints (`river` with `CUSTOM_FILE`, `cdr_forcing_file`). Those files are not stored in the repository.
