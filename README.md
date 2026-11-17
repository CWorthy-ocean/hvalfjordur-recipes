# hvalfjordur-recipes

Companion repository to the manuscript on modelling ocean alkalinity enhancement (OAE) in Hvalfjörður, Iceland. It holds the recipes to set up and run the nested ROMS-MARBL simulations with [C-Star](https://github.com/CWorthy-ocean/C-Star), and the notebooks behind the model evaluation and the OAE analysis.

It replaces [C-Star-in-Hvalfjordur](https://github.com/CWorthy-Ocean/C-Star-in-Hvalfjordur), which set the model up with the earlier roms-tools notebooks.

## Layout

```
setup/      per-domain forge blueprints, workplans and inputs prepared outside forge (Iceland0–3)
data/       observed data: staging notebook, field data files; raw/ and staged/ are not tracked
analysis/   model–observation comparison and OAE analysis notebooks, and the roms_regrid.py helper
docs/       introduction page of the documentation site
images/     photographs and logos used by the documentation site
archive/    files from the old layout, kept locally and not tracked (see archive/README.md)
```

## Workflow

1. **Set up and run the model.** See [setup/README.md](setup/README.md) for the nesting chain (Iceland0 2.5 km → Iceland1 750 m → Iceland2 200 m → Iceland3 50 m), what each domain folder contains, and the order of operations.
2. **Stage the observations.** [data/obs_data_staging.ipynb](data/obs_data_staging.ipynb) downloads the SEANOE Hvalfjörður datasets into `data/raw/` and unpacks them into `data/staged/`.
3. **Analyze.** The notebooks in [analysis/](analysis/):

| Notebook | Content |
|---|---|
| `site_description.ipynb`, `grid_overview.ipynb`, `wind_conditions.ipynb` | Site, nested grids, wind and tidal conditions |
| `ssh_comparison.ipynb`, `velocity_analysis.ipynb` | Sea level and currents vs. tide gauge and ADCP |
| `ctd_comparison.ipynb`, `bgc_analysis.ipynb`, `pCO2_bias_calculation.ipynb` | Hydrography, carbonate system and nutrients vs. CTD, bottle and mooring data |
| `sf6_observations.ipynb`, `sf6_model.ipynb` | SF₆ tracer release: observations and modelled dye |
| `model_solution.ipynb` | Currents in the Iceland3 solution |
| `mixed_layer_depth.ipynb` → `OAE_ensemble.ipynb` → `oae_analysis.ipynb` | OAE ensemble (CDR1–6): mixed-layer depth, pre-processing into intermediate files, figures |
| `detectability_limits.ipynb` | Detectability limits of the OAE signal |

The notebooks run on Anvil and read model output and intermediate files from absolute paths there; adapt the paths in each notebook's configuration cell to run them elsewhere.

## Documentation site

The notebooks are published as a [MyST / Jupyter Book](https://mystmd.org) site; `myst.yml` defines the table of contents.

1. Create a Python environment and install the documentation requirements: `pip install -r requirements.txt`
2. Build the site with `jupyter-book build --html`, or preview it locally with `jupyter-book start`.

`.github/workflows/deploy.yml` builds the site and deploys it to GitHub Pages on every push to `main`.

## Status

Work in progress towards resubmission:
- The setup folder is a draft; several workplans and helper scripts are still to be added (see [setup/README.md](setup/README.md)).
- The reorganized OAE notebooks have not yet been re-run on the Anvil output.
