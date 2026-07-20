---
title: 'pyoceanmap: Physics-informed objective mapping of sparse in-situ ocean observations'
tags:
  - Python
  - oceanography
  - objective mapping
  - gridding
  - hydrography
  - Arctic Ocean
authors:
  - name: Simran Suresh
    orcid: 0009-0004-0477-1600
    affiliation: 1
affiliations:
  - name: University of Graz, Austria
    index: 1
date: 17 July 2026
bibliography: paper.bib
---

## Summary

Oceanographic observations are typically sparse, irregularly distributed in space and time,
and collected from diverse platforms such as ship-based CTD profiles, moorings, and autonomous
floats. Converting these observations into gridded fields is essential for analyzing ocean
circulation, stratification, and climate variability. Objective mapping or optimal interpolation [@bretherton1976] is a standard technique for this purpose, but implementations are often
fragmented and cumbersome. The method is tightly coupled to specific datasets, and not published as reusable software.

`pyoceanmap` is a Python package that provides a reproducible, end-to-end workflow for mapping
hydrographic observations onto spatial grids. It integrates data preprocessing, physical
variable computation (dynamic height and freshwater content, via TEOS-10 [@ioc2010teos10]), and
a two-stage, physics-informed objective mapping scheme into a modular pipeline. The mapping
scheme incorporates both geographic distance and potential-vorticity similarity between
observations and grid points for weighting, using bathymetry from the International Bathymetric Chart of the Arctic Ocean (IBCAO) [@jakobsson2020ibcao]. It is demonstrated to the polar ocean - the Arctic but can be suited to ocean applications, where sparse sampling and strong bathymetric control demand interpolation that depends on the underlying dynamics rather than smoothing across them.

## Statement of Need

Objective mapping is well established in physical oceanography, but practical implementations pose serious constraints that are hard to reuse, validate, or extend. A general, reusable
implementation must address several requirements together:

- irregularly spaced observations;
- physical constraints such as potential vorticity, not just geographic distance;
- temporal variability between observations taken years apart;
- bathymetric information integrated into the interpolation;
- reproducibility, from raw text files to a gridded field, in a single pipeline.

`pyoceanmap` targets to overcome the limitations in one package. 

## Comparison to Existing Tools

Several existing Python packages support ocean data analysis but address a different problem
than `pyoceanmap`:

- **OceanSpy** [@oceanspy] is an `xarray`-native package for analyzing and visualizing
  *model* output (primarily from MITgcm), providing diagnostics such as heat and salt budgets and
  particle tracking on regular model grids. It assumes the data are already processed on a grid.
- **Seaduck** [@seaduck] performs Eulerian and Lagrangian interpolation on ocean *datasets*
  (typically gridded model output), including particle tracking through model velocity fields.
  The interpolation scheme is geometric and operates on existing structured datasets rather than
  mapping sparse in-situ observations onto a new grid.
- Generic interpolation utilities (`scipy.interpolate`, `xarray`/`xESMF` regridding) solve the
  geometric problem including regridding between two *known* grids, but have no notion of
  oceanographic dynamics, so they apply no potential-vorticity or bathymetric constraints.

`pyoceanmap` therefore addresses these gaps by turning sparse, irregular
in-situ profiles into a gridded field in the first place, using a physics-informed (potential
vorticity- and bathymetry-aware) objective mapping scheme rather than a purely geometric
interpolation. To our knowledge, no existing open-source Python package implements this specific
combination for in-situ hydrographic data.

## Features

- **End-to-end workflow**: merge raw hydrographic text files, compute derived variables,
  generate a projected grid, and perform objective mapping within a single package.
- **Physics-informed interpolation**: two-stage objective mapping using spatial distance,
  potential-vorticity constraints, and temporal decorrelation.
- **Bathymetry integration**: IBCAO depth lookup via a k-d tree for efficient nearest-neighbor
  queries.
- **Derived variables**: dynamic height and freshwater content, computed via the TEOS-10
  standard (through the `gsw` package).
- **Modular design**: each stage (preprocessing, grid generation, bathymetry, observables,
  mapping) can be used independently or composed into a full pipeline.

## Usage

```python
from pyoceanmap import (
    merge_txt_to_csv,
    generate_arctic_grid,
    add_depth_to_grid,
    compute_dynamic_height,
    objective_map,
)

merge_txt_to_csv("./data/", "merged.csv")

compute_dynamic_height("merged.csv", "data_points.csv")

generate_arctic_grid("grid.csv", dx=50_000)

add_depth_to_grid("grid.csv", "grid.csv", nc_file="IBCAO_v4_2_13_400m.nc")

objective_map(
    data_csv="data_points.csv",
    grid_csv="grid.csv",
    output_csv="mapped.csv",
    target_time="2013-09-01",
    observable="Surf_DH",
)
```

`pyoceanmap` has been applied to two case studies - mapping Arctic Ocean dynamic height and
freshwater content from UDASH hydrographic observations [@behrendt2018udash] to characterize
the Beaufort Gyre and Transpolar Drift, and mapping Southern Ocean dynamic height from Argo
float measurements [@reeve2016] to characterize the Weddell and Ross Gyres (see `figures/` in
the repository).

## Research Impact

`pyoceanmap` has been used to produce results presented in two research posters:

- S. Suresh, B. Rabe, C. Wekerle, and T. Kanzow, "Central Arctic Ocean circulation dynamics
  under changing freshwater regimes," Geophysical Fluid Dynamics Summer School, Paris, May 2024.
- S. Suresh, B. Rabe, and C. Wekerle, "Past decadal changes in the Transpolar Drift stream,"
  Polar Marine Science Gordon Research Conference, March 2025.

Separately, the underlying two-stage, potential-vorticity- and bathymetry-aware objective
mapping *methodology* implemented here was originally developed and applied in MATLAB, where it
supported the Arctic Ocean freshwater content assessment of @rabe2011freshwater and the
basin-scale liquid freshwater storage trend analysis of @rabe2014, and the same method was
applied to the Southern Ocean to grid upper-ocean hydrographic properties in the Weddell Gyre
from Argo float measurements [@reeve2016]. `pyoceanmap` is a from-scratch, open-source Python
reimplementation of that methodology; it has not itself been used in those publications, and
this distinction is stated here explicitly rather than implied.

## AI Usage Disclosure

The core scientific and numerical code in this package — hydrographic data preprocessing,
TEOS-10-based dynamic height and freshwater content calculations, grid generation, bathymetric
integration, and the physics-informed objective mapping algorithm (potential-vorticity- and
bathymetry-aware covariance modeling) was designed and written entirely by the author without
AI assistance. AI assistance (Claude Code, Anthropic) was used for the restructuring the prototype into an installable package, configuring Sphinx documentation, and rephrasing this paper and the README, all under the author's direction and review.

## Acknowledgements

This work builds on the objective analysis framework introduced by Bretherton, Davis, and
Fandry [@bretherton1976]. The implementation uses TEOS-10 conventions for thermodynamic
calculations [@ioc2010teos10] and IBCAO bathymetric data for Arctic Ocean applications
[@jakobsson2020ibcao].

## References
