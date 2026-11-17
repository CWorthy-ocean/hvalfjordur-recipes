# Introduction

This is the companion to the manuscript on modelling ocean alkalinity enhancement (OAE) in Hvalfjörður, Iceland. It collects the recipes used to set up and run a nested Regional Ocean Modeling System (ROMS-MARBL) configuration with [C-Star](https://github.com/CWorthy-ocean/C-Star), the notebooks that compare the model with field observations, and the analysis of the OAE experiments.

% A figure of a photograph of some mountains, followed by a caption
:::{figure} ../images/20240718_THRAINN_534860.jpg
:label: fig:fjord

A photograph of Hvalfjörður, Iceland. July 2024
:::

## Model setup

The configuration uses four nested grids to resolve the transition from the open North Atlantic to the fjord-scale dynamics of Hvalfjörður:

| Domain | Region | Horizontal resolution |
|---|---|---|
| Iceland0 | North Atlantic around Iceland | 2.5 km |
| Iceland1 | Southwest Iceland | 750 m |
| Iceland2 | Icelandic shelf and the approaches to Hvalfjörður | 200 m |
| Iceland3 | Hvalfjörður | 50 m |

Each domain is described by a C-Star **forge blueprint**, and its runs by one or more **workplans** (`setup/Iceland{n}/`); see [](../setup/README.md) for the full list and the order of operations. A few inputs are prepared outside forge:

- **`Iceland2_river_forcing.ipynb`**: builds the custom river forcing file for Iceland2.
- **`passive_tracer_setup.ipynb`**: adds a passive dye tracer to an Iceland2 run and prepares consistent initial and boundary conditions for the tracer experiment, the model analogue of the SF₆ release.
- **`CDR_forcing_creation.ipynb`**: builds the alkalinity-release (CDR) forcing for the Iceland3 OAE ensemble members CDR1–6.

## Observations

- **`obs_data_staging.ipynb`**: downloads the SEANOE Hvalfjörður datasets (CTD profiles, discrete samples, mooring CTD and ADCP data) into `data/raw/` and unpacks them into `data/staged/`.

## Site and grids

- **`site_description.ipynb`**: site-description plots for Hvalfjörður: bathymetry, regional setting, local forcing (wind roses, sea-level anomalies), and the locations of the CTD casts and moorings used for model validation.
- **`grid_overview.ipynb`**: maps the outlines of the four nested grids.
- **`wind_conditions.ipynb`**: wind forcing and sea-surface-height variability during the July and November windows of the Iceland3 simulation, including tidal-range statistics, to characterize the conditions of the release windows.

## Model–observation comparison

- **`ssh_comparison.ipynb`**: compares Grundartangi tide-gauge sea level with the modelled sea-surface height.
- **`velocity_analysis.ipynb`**: compares observed currents (ADCP) with ROMS output: time series, current roses, spectra of tidal and subtidal variability, and vertical profiles.
- **`ctd_comparison.ipynb`**: compares the SEANOE CTD profiles and HAFRO station time series in Hvalfjörður with the Iceland2 solution: temperature and salinity profiles, sections and monthly evolution, chlorophyll and oxygen.
- **`bgc_analysis.ipynb`**: compares observed (SEANOE discrete samples) and modelled dissolved inorganic carbon, alkalinity, nutrients and oxygen at the HV stations along Hvalfjörður, and the moored pCO₂ sensor with the modelled surface pCO₂ (November 2024).
- **`pCO2_bias_calculation.ipynb`**: quantifies the surface pCO₂ bias that follows from mean-state errors in the model.
- **`sf6_observations.ipynb`**: the SF₆ tracer observations from the July 2024 field trial, where SF₆ was released as a passive analogue of an alkalinity plume.
- **`sf6_model.ipynb`**: compares the modelled passive dye (Iceland2) with the observed SF₆.

## Model solution

- **`model_solution.ipynb`**: currents in the Iceland3 solution in Hvalfjörður: time-mean velocities on depth levels, as maps and sections.

## Ocean alkalinity enhancement

The six ensemble members release alkalinity in July (CDR1–3) or November (CDR4–6) 2024. Run the notebooks in this order:

- **`mixed_layer_depth.ipynb`**: the seasonal mixed-layer depth following Stevens (2010), used to compute the fraction of added alkalinity in the mixed layer.
- **`OAE_ensemble.ipynb`**: turns the ROMS output of the ensemble into the intermediate files (inventories, CDR metrics, extrema, mean fields, snapshots) that the analysis plots.
- **`oae_analysis.ipynb`**: the OAE figures: added alkalinity and its mixed-layer fraction, surface fields and extrema, sensitivity to the carbonate background, cumulative CO₂ uptake and CDR efficiency, and release snapshots.
- **`detectability_limits.ipynb`**: detectability limits for the OAE signal, from the variability of mooring pH, alkalinity and DIC at station HV10, and moored pCO₂.
