# Model setup

This folder holds everything needed to create and run the nested ROMS-MARBL simulations with [C-Star](https://github.com/CWorthy-ocean/C-Star):

- **Forge blueprints** (`*.forge_blueprint.yaml`) describe a domain: grid, time step, partitioning, forcing sources and code versions. `cstar forge` turns a blueprint into model inputs and a run blueprint.
- **Workplans** (`wp_*.yaml`) chain runs: spin-up and yearly segments, nesting a child domain in its parent (`nest_ic`, `nest-from`), and continuing from restarts.
- **Notebooks and scripts for steps forge does not do**, such as the custom river files, the passive-tracer setup and the OAE (CDR) release forcing. Their outputs are passed to the blueprints as custom files.

The roms-tools setup notebooks used for the initial submission (`setup_iceland0-3.ipynb`) are deprecated and kept in `archive/notebooks/setup/`.

> **Draft.** Not all blueprints and workplans are in place yet. [Experiments in the manuscript](#experiments-in-the-manuscript) lists every experiment and the files it is still missing; the tables under [Contents by domain](#contents-by-domain) list each folder's files.

## Nesting chain

| Domain | Region | Grid | Δx | Δt | Simulated period | Parent |
|---|---|---|---|---|---|---|
| Iceland0 | North Atlantic around Iceland | 512 × 512 × 60, 1280 × 1280 km | 2.5 km | 180 s | 2023-01-01 – 2024-12-31 | GLORYS (open boundaries) |
| Iceland1 | First nest, southwest Iceland | 512 × 384 × 60, 384 × 288 km | 750 m | 60 s | 2023-01-02 – 2024-12-31 | Iceland0 |
| Iceland2 | Icelandic shelf and the approaches to Hvalfjörður | 512 × 512 × 60, 102.4 × 102.4 km | 200 m | 15 s | 2023-02-01 – 2024-12-31 | Iceland1 |
| Iceland3 | Hvalfjörður (fjord scale) | 640 × 384 × 60, 32 × 19.2 km | 50 m | 5 s | 2024-06-15 – 2024-11-30 | Iceland2 |

These are the values in each forge blueprint; workplan steps can override the dates and the time step. All domains use θs = 5, θb = 2, hc = 300 m, surface forcing from ERA5 and tides from TPXO (15 constituents).

## Experiments in the manuscript

Each experiment is listed with its status:
- **complete**: every file needed to rerun it is in this folder;
- **partial**: some files are present and others still have to be added;
- **drafted**: the files are written but not yet forged or run;
- **missing**: no setup files are here yet.

Dates come from the blueprints, workplans and forcing notebooks. The last column names the analysis notebooks that read each experiment's output. Several of those notebooks still read the output of the older roms-tools runs (`Iceland2_MARBL_2024_60m`, `Iceland3_MARBL_2024`). They will have to be pointed at the C-Star runs once those are rerun.

### Base runs

| Experiment | Period | In this folder | Missing | Status | Read by |
|---|---|---|---|---|---|
| **Iceland0** | 2023-01-01 – 2024-12-31 | blueprint; workplan `wp_Iceland0_glodap_woa.yaml` | — | complete | `grid_overview` |
| **Iceland1** | 2023-01-15 – 2024-12-31 (nested from the Iceland0 restart of 2023-01-15) | blueprint; workplan `wp_Iceland1_glodap_woa.yaml` | `merge_cdrgas_dirs.py`, which the workplan needs to read Iceland0's boundary output. Iceland2 nests in the run `iceland1_new` (forge blueprint `pio-dev_Iceland1_hires_256procs`); confirm whether these files describe that run, or add its blueprint and workplan | partial | `grid_overview` |
| **Iceland2** | 2023-02-02 – 2024-12-31 | blueprint (custom rivers); `Iceland2_river_forcing.ipynb`; workplan `Iceland2_timechuncked_customriver.yaml` (run `iceland2_customriver`, nested in `iceland1_new`). Rerun nested in `iceland1_glodap_woa`, drafted: `Iceland2_glodap_woa.forge_blueprint.yaml`, `wp_Iceland2_glodap_woa.yaml` | rerun: the rebuilt river file (run the corrected `Iceland2_river_forcing.ipynb` on Anvil) | complete | `ctd_comparison`, `bgc_analysis` (run `iceland2_customriver`); `ssh_comparison`, `velocity_analysis` and the pCO₂ mooring figure in `bgc_analysis` still read `Iceland2_MARBL_2024_60m` |
| **Iceland3_July** | July 2024 (the blueprint covers 2024-06-15 – 2024-11-30). Run on Tanagra as `iceland3-jul2024`; its output is copied to Anvil (`/home/x-uheede/S/cstar/Iceland3_july_output/iceland3-jul2024`) | blueprint (custom rivers) | the July workplan used on Tanagra; `Iceland3_river_forcing.ipynb`; `correct_alk_dic.py`, if July nests in corrected Iceland2 output like November does | partial | `model_solution`, `wind_conditions` (older run `Iceland3_MARBL_2024`) |
| **Iceland3_November** | 2024-11-01 – 2024-11-30 | blueprint; workplan `wp_Iceland3_corr.yaml` | `Iceland3_river_forcing.ipynb`; `correct_alk_dic.py`, which the workplan's ALK/DIC correction refers to | partial | `wind_conditions` (older run `Iceland3_MARBL_2024`) |

### Speciality experiments

| Experiment | Period | In this folder | Missing | Status | Read by |
|---|---|---|---|---|---|
| **Iceland2_dye_tracer** | July 2024, from the Iceland2 restart of 2024-07-17 13:00 | `passive_tracer_setup.ipynb`: adds the dye to that restart and zero dye to the boundary files | blueprint/workplan for the dye run (the original run, `Iceland2_NOMARBL_2024_DYE_2`, used the roms-tools setup) | partial | `sf6_model` |
| **Iceland2_10min_velocity_output** | 2024-07-02 – 2024-08-01 (not run yet), from the 2024-07-02 restart of `iceland2_customriver` | physics-only (no MARBL) blueprint `Iceland2_physics_10min_velocity.forge_blueprint.yaml`; workplan `wp_Iceland2_10min_velocity.yaml`: hourly restarts, 10-minute averages of u, v, w; boundaries as `iceland2_customriver` segment7 | — (drafts, not yet forged or run) | drafted | planned for the ADCP comparison in `velocity_analysis`, which for now reads `Iceland2_MARBL_2024_60m` |
| **Iceland3_CDR_ens1** (July) | 2024-07-09 – 07-23, from the `iceland3-jul2024` restart of 07-09; release records 07-12 – 07-15 | `CDR_forcing_creation.ipynb` (ENS1, and the 14-day C-Star file); `make_cdr_build.py` (the November build); workplan `wp_Iceland3_oae_ens1.yaml` | — (not run yet) | drafted | `mixed_layer_depth`, `OAE_ensemble`, `oae_analysis`, once pointed at these runs (see "OAE analysis of the C-Star runs" below) |
| **Iceland3_CDR_ens2** (July) | 2024-07-11 – 07-25; release records 07-14 – 07-17 | as ens1; workplan `wp_Iceland3_oae_ens2.yaml` | — (not run yet) | drafted | as ens1 |
| **Iceland3_CDR_ens3** (July) | 2024-07-13 – 07-27; release records 07-16 – 07-19 | as ens1; workplan `wp_Iceland3_oae_ens3.yaml` | — (not run yet) | drafted | as ens1 |
| **Iceland3_CDR_ens4** (November) | 2024-11-02 – 11-16, from the `iceland3-nov2024` restart of 11-02; release records 11-05 – 11-08 | `CDR_forcing_creation.ipynb` (ENS4, and the 14-day C-Star file); `make_cdr_build.py`; workplan `wp_Iceland3_oae_ens4.yaml` | — (not run yet) | drafted | as ens1 |
| **Iceland3_CDR_ens5** (November) | 2024-11-06 – 11-20; release records 11-09 06:00 – 11-12 06:00 | as ens4; workplan `wp_Iceland3_oae_ens5.yaml` | — (not run yet) | drafted | as ens4 |
| **Iceland3_CDR_ens6** (November) | 2024-11-14 – 11-28; release records 11-17 – 11-20 | as ens4; workplan `wp_Iceland3_oae_ens6.yaml` | — (not run yet) | drafted | as ens4 |

The CDR ensemble members go by different names in different places:
- **ens*n*** in the manuscript;
- **ENS*n*** in `CDR_forcing_creation.ipynb`;
- **CDR*n*** in the analysis notebooks and run directories (`Iceland3_MARBL_2024_CDRn`).

Each member has a 4-day (96 h) alkalinity release inside its forcing window.

### Files still to add

| Folder | File | Needed by |
|---|---|---|
| `Iceland1/` | `merge_cdrgas_dirs.py` | Iceland1 |
| `Iceland1/` | blueprint and workplan of `iceland1_new`, the Iceland1 run Iceland2 nests in, if it is not the run the files here describe | Iceland2 and everything nested in it |
| `Iceland2/` | dye-run workplan | Iceland2_dye_tracer |
| `Iceland3/` | `Iceland3_river_forcing.ipynb` | all Iceland3 experiments |
| `Iceland3/` | `correct_alk_dic.py` | Iceland3_November (and Iceland3_July, if it uses the same correction) |
| `Iceland3/` | the July workplan used on Tanagra (`iceland3-jul2024`) | Iceland3_July |

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
| `Iceland2_river_forcing.ipynb` | Builds the Iceland2 river forcing file on Anvil. GloFAS rivers (daily, roms-tools default BGC concentrations) plus the Hvalfjörður rivers (custom dataset, Table S1 concentrations); every river gets the 0–10 °C temperature cycle. Corrected version: the earlier one saved the Hvalfjörður rivers alone | present (run on Anvil 2026-11-19) |
| `passive_tracer_setup.ipynb` | Adds a passive dye tracer to an Iceland2 run (initial and boundary files), the model analogue of the SF₆ release | present |
| `Iceland2_timechuncked_customriver.yaml` | Workplan for the 2023–2024 run (`iceland2_customriver`): `nest_ic` from the `iceland1_new` restart of 2023-02-02 → spin-up → segments 1–8, each nested in the matching `iceland1_new` segment | present |
| `Iceland2_physics_10min_velocity.forge_blueprint.yaml` | Physics-only (no MARBL) copy of the Iceland2 blueprint for July 2024: hourly restarts, 10-minute averages of u, v, w, no history or child-boundary output | draft |
| `wp_Iceland2_10min_velocity.yaml` | Workplan for that run: starts from the `iceland2_customriver` restart of 2024-07-02, boundaries from `iceland1_new` segment7 | draft |
| `make_river_ts_only.py` | Writes the temperature/salinity-only copy of the custom river file that the physics-only blueprint uses (a build without MARBL reads 2 river tracers; the original has 34) | present |
| `Iceland2_glodap_woa.forge_blueprint.yaml` | Forge blueprint for the Iceland2 rerun nested in `iceland1_glodap_woa`. Same grid and forcing as the custom-river blueprint, plus: the rebuilt river file; ucla-roms `constant_Fe` (1000 forcing files); `pio_stride` 64. Output: hourly history snapshots of zeta, ubar, vbar, u, v; daily snapshots of the BGC tracers and diagnostics (with `pH_3D`, without the `_ALT_CO2` diagnostics: no OAE in this run); daily restarts (T and S come from these) | draft |
| `wp_Iceland2_glodap_woa.yaml` | Workplan for that run: `nest_ic` from the `iceland1_glodap_woa` restart of 2023-02-01 → spin-up to 2023-02-15 (dt 10 s, 12 h) → four segments to 2024-12-31 (dt 25 s, 48 h); 4 × 64 cores, allocation EES260142 | draft |
| `link_forge_inputs.sh` | Hard-links the custom-river forge run's grid, surface, restoring and tidal inputs into the new forge working directory under the new names, so forge reuses them | present |
| `gather_child_bry.py` | Collects Iceland1's child_bry files into one folder in time order, then gives each workplan step a folder of links to the files covering its dates | present |
| `wp_Iceland2_dye.yaml` | Workplan for the passive-tracer run used in `analysis/sf6_model.ipynb` | to add |

### `Iceland3/`

| File | Role | Status |
|---|---|---|
| `Iceland3_256procs.forge_blueprint.yaml` | Forge blueprint nested in Iceland2, river forcing from a custom file, no CDR forcing (`cdr: none`) | present |
| `wp_Iceland3_corr.yaml` | Workplan: `nest_ic` from the corrected Iceland2 restart → November 2024 run | present |
| `CDR_forcing_creation.ipynb` | Builds the OAE (alkalinity release) forcing for the ensemble members CDR1–6. Its last two sections write the files for the C-Star runs of ENS4–6 and ENS1–3: the same releases on the C-Star Iceland3 grid, padded with zero flux to 15 days, CDF5 | present (C-Star sections not yet run) |
| `make_cdr_build.py` | Copies the compile-time folder of the `iceland3-nov2024` run blueprint and defines CDR_FORCING in its `cppdefs.opt`; all six OAE workplans point `code.compile_time` at the copy | present |
| `wp_Iceland3_oae_ens4.yaml`, `wp_Iceland3_oae_ens5.yaml`, `wp_Iceland3_oae_ens6.yaml` | OAE members ENS4–6 (CDR4–6): the `iceland3-nov2024` run blueprint from its restart at each member's start, for 14 days, with overrides for CDR forcing, the hourly CDR output stream and the BGC output the OAE analysis reads | draft |
| `wp_Iceland3_oae_ens1.yaml`, `wp_Iceland3_oae_ens2.yaml`, `wp_Iceland3_oae_ens3.yaml` | OAE members ENS1–3 (CDR1–3), set up like ENS4–6: the same run blueprint and overrides, from a restart of the July run (`iceland3-jul2024`, run on Tanagra), nested in Iceland2 boundary files that cover July | draft |
| `Iceland3_river_forcing.ipynb` | Builds the custom Iceland3 river forcing file. The code is still in `archive/notebooks/setup/setup_iceland3.ipynb` (river section). | to add |
| `correct_alk_dic.py` | Corrects the Iceland2 ALK/DIC inputs (f = 0.51, ρ = 1027) before nesting; referenced by `wp_Iceland3_corr.yaml` | to add |
| `wp_Iceland3_jul2024.yaml` | Workplan for the July 2024 run (`iceland3-jul2024`, run on Tanagra; the window of CDR1–3) | to add |

## Order of operations

1. **Iceland0:** run `wp_Iceland0_glodap_woa.yaml`.
2. **Iceland1:** run `wp_Iceland1_glodap_woa.yaml`. Its `nest_ic` step interpolates the Iceland0 restart; its run steps read Iceland0's child boundary files.
3. **Iceland2:**
   - **Base run:** run `Iceland2_river_forcing.ipynb`, forge the blueprint, then run `Iceland2_timechuncked_customriver.yaml`.
   - **Rerun nested in `iceland1_glodap_woa` (draft):** run `Iceland2_river_forcing.ipynb` on Anvil (it writes the river file), then `link_forge_inputs.sh --link` and forge `Iceland2_glodap_woa.forge_blueprint.yaml`. Then run `gather_child_bry.py` (Iceland1's child_bry files, one folder per step) and `../check_nest_bracketing.py`, and run `wp_Iceland2_glodap_woa.yaml`.
   - **Dye run:** run `passive_tracer_setup.ipynb` first.
   - **10-minute velocity run:** make the T/S-only river file with `make_river_ts_only.py`, forge `Iceland2_physics_10min_velocity.forge_blueprint.yaml`, then run `wp_Iceland2_10min_velocity.yaml` once the base run has written its July restarts.
4. **Iceland3:** build the river file, forge the blueprint, correct the Iceland2 ALK/DIC (`correct_alk_dic.py`), then run `wp_Iceland3_corr.yaml` (November) and the July workplan.
   - **November OAE members (ENS4–6):** run the last section of `CDR_forcing_creation.ipynb` (the 14-day C-Star files). Run `make_cdr_build.py` on the `iceland3-nov2024` run blueprint (the CDR_FORCING build). Then run `wp_Iceland3_oae_ens4.yaml`, `wp_Iceland3_oae_ens5.yaml` and `wp_Iceland3_oae_ens6.yaml`; each is independent.
   - **July OAE members (ENS1–3):** run the "July members for the C-Star runs" section of `CDR_forcing_creation.ipynb`. The CDR_FORCING build of the November members must exist. Check each workplan with `../check_nest_bracketing.py`, then run `wp_Iceland3_oae_ens1.yaml`, `wp_Iceland3_oae_ens2.yaml` and `wp_Iceland3_oae_ens3.yaml`; each is independent.
5. Post-processing and figures: see `analysis/` (for the OAE ensemble: `mixed_layer_depth.ipynb` → `OAE_ensemble.ipynb` → `oae_analysis.ipynb`).

## Conventions and open points

- **File names.** Blueprints are named after the forge run that produced them, which is why the names vary. A later clean-up could rename them to `Iceland{n}.forge_blueprint.yaml`; the `name:` and `working_dir:` fields inside would need the same change.
- **Paths.** Workplans currently point at absolute Anvil paths: the run blueprints forge generated (`.../blueprints/B_*.yaml`), restart files and child-boundary folders. They document what was run, but cannot be used elsewhere as they are. Deciding whether to point them at the blueprints in this folder (or to document the forge step that produces each `B_*.yaml`) is open.
- **Iceland1 parent of Iceland2.** `Iceland2_timechuncked_customriver.yaml` nests Iceland2 in the run `iceland1_new`, built from the forge blueprint `pio-dev_Iceland1_hires_256procs`. The Iceland1 blueprint and workplan in `Iceland1/` (`Iceland1_256procs`, `wp_Iceland1_glodap_woa.yaml`, run `iceland1_glodap_woa`) may describe a different run; this needs confirming.
- **Model code.** The Iceland2 and Iceland3 blueprints use the `constant_Fe` branch of ucla-roms; Iceland0 and Iceland1 use `main`. The Iceland1 workplan overrides ucla-roms to 0.13.1, because it needs more than 360 boundary files. Since commit `fc2b6d84`, `constant_Fe` reads up to 1000 forcing files instead of 360. Pin the branch name, not a commit hash. For any ref that isn't a release tag, Forge writes the newest (0.9+) namelist. At run time, C-Star maps a commit hash to the release it descends from (0.8.0) and rejects that namelist. The 0.9+ namelist names the CDR tracer output section `CDR_LITE_OUTPUT_SETTINGS`, so `constant_Fe` (0.8.0-based) has to run without its `CDR_TRACER_OUTPUT_SETTINGS`. It aborted on that until the branch learned to treat the missing section as output off. ROMS ignores files past the limit without an error, so each step of `wp_Iceland2_glodap_woa.yaml` reads only its own share of Iceland1's boundary files (about 370 per six months).
- **Iceland2 river file.** The earlier version of `Iceland2_river_forcing.ipynb` wrote `riv` (the 16 Hvalfjörður rivers alone) as `Iceland2_river_combied.nc`, the file the `iceland2_customriver` runs used, not the GloFAS + Hvalfjörður combination it computed. Its combination step had bugs as well: overlapping `river_index` numbers, and GloFAS volumes left in place inside the fjord. Its last run (2026-09-11) also predates its Table S1 nutrient values. The notebook is corrected; `Iceland2_glodap_woa` uses its output. Table S1 describes the Hvalfjörður rivers; the GloFAS rivers carry the roms-tools default concentrations.
- **OAE members without forge.** The OAE members are the base run plus a release, so they need no forge blueprint of their own. Each workplan reuses the base run's run blueprint and overrides four things:
  - the compile-time folder (`make_cdr_build.py`): CDR_FORCING is a cppdef, which only `cppdefs.opt` can set;
  - `cdr_forcing`, the release file;
  - the namelist groups `cdr_frc_settings` and `cdr_output_settings`;
  - the MARBL output lists.

  The CDR output stops ROMS at startup unless the MARBL diagnostics list includes FG_CO2, FG_ALT_CO2, pCO2SURF, pCO2SURF_ALT_CO2, CO3, CO3_ALT_CO2, co3_sat_arag, co3_sat_calc, zsatarag and zsatcalc. ROMS stops when model time passes the last record of any forcing file, so a CDR file has to reach past the end of its run.
- **OAE analysis of the C-Star runs.** Two things change when the analysis notebooks are pointed at the C-Star OAE runs:
  - The earlier runs wrote the CDR output stream as `*_cstar.*.nc`; ucla-roms now writes it as `*_cdr.*.nc` (`CDR_OUTPUT_SETTINGS`). `OAE_ensemble.ipynb` looks for `cstar` files.
  - `release_start_hours` in `oae_analysis.ipynb` counts from each member's first model record. The C-Star members switch the flux on and off at the forcing records, with no ramp (`cdr_time_interpolation` off), and each starts at the start of its forcing window, so the flux switches on 72 h in (78 h for CDR5). All six values change: from 36, 70, 70, 48, 54, 48 h (the earlier runs) to 72, 72, 72, 72, 78, 72 h.
- The custom-forcing notebooks write NetCDF files whose paths go into the blueprints (`river` with `CUSTOM_FILE`, `cdr_forcing_file`) or the workplans (`cdr_forcing`). Those files are not stored in the repository.
