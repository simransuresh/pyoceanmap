"""
Self-contained pyoceanmap tutorial (no external data required).

This script fabricates a small, physically plausible synthetic hydrographic
dataset and runs the *entire* pyoceanmap pipeline on it:

    1. write synthetic UDASH-style .txt profiles
    2. merge_txt_to_csv        -> one merged CSV
    3. compute_dynamic_height  -> surface dynamic height per station (TEOS-10)
    4. generate_arctic_grid    -> a coarse polar grid
    5. add_depth_to_grid       -> attach bathymetry (from a tiny synthetic IBCAO file)
    6. objective_map           -> map the observations onto the grid
    7. plot observed vs. mapped fields

Because it needs no downloads, it runs anywhere in a few seconds and is a good
first thing to try after `pip install -e .`. For the real Arctic UDASH / IBCAO
workflow, see ``end2end_demo.ipynb``.

Run:
    python examples/tutorial_synthetic.py
"""

import os

import numpy as np
import pandas as pd

from pyoceanmap import (
    merge_txt_to_csv,
    compute_dynamic_height,
    compute_freshwater,
    generate_arctic_grid,
    add_depth_to_grid,
    objective_map,
)

# ----------------------------------------------------------------------
# Reproducibility + output location
# ----------------------------------------------------------------------
RNG = np.random.default_rng(42)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
DATA = os.path.join(OUT, "data")
os.makedirs(DATA, exist_ok=True)


# ----------------------------------------------------------------------
# 1. Fabricate synthetic UDASH-style hydrographic profiles
# ----------------------------------------------------------------------
def make_synthetic_txt(path, n_stations=70, seed_offset=0):
    """
    Write one whitespace-delimited file in the UDASH column layout that
    ``merge_txt_to_csv`` expects. Each station is a full 0-500 m profile
    with a smoothly varying surface salinity (so dynamic height varies
    smoothly in space and the objective mapping has real structure to
    interpolate).
    """
    rng = np.random.default_rng(100 + seed_offset)

    header = (
        "yyyy-mm-ddThh:mm Latitude_[deg] Longitude_[deg] "
        "Pressure_[dbar] Depth_[m] Temp_[°C] Salinity_[psu]"
    )
    lines = [header]

    z_levels = np.arange(0, 501, 20)  # 0,20,...,500 m

    for s in range(n_stations):
        lat = 75.0 + 9.0 * rng.random()          # 75-84 N
        lon = -30.0 + 60.0 * rng.random()        # 30 W - 30 E
        month = rng.integers(1, 13)
        day = rng.integers(1, 28)

        # smooth spatial gradient in surface salinity -> smooth DH field
        surf_sal = 30.0 + 0.3 * (lat - 75.0) + 0.03 * (lon + 30.0)

        for z in z_levels:
            # salinity increases toward a deep value; temperature is a
            # warm intermediate layer decaying with depth (Arctic-like)
            sal = surf_sal + (34.9 - surf_sal) * min(z / 400.0, 1.0)
            temp = -1.6 + 2.5 * np.exp(-z / 150.0) + 0.05 * rng.standard_normal()
            pres = float(z)  # pressure ~ depth (dbar) is fine here

            lines.append(
                f"{2013:04d}-{month:02d}-{day:02d}T00:00 "
                f"{lat:.4f} {lon:.4f} {pres:.1f} {float(z):.2f} "
                f"{temp:.3f} {sal:.4f}"
            )

    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


print("1. Writing synthetic UDASH-style .txt files ...")
make_synthetic_txt(os.path.join(DATA, "synthetic_2013.txt"))


# ----------------------------------------------------------------------
# 2. Merge raw text -> CSV
# ----------------------------------------------------------------------
print("2. Merging text files -> merged.csv ...")
merged_csv = os.path.join(OUT, "merged.csv")
merge_txt_to_csv(DATA, merged_csv)


# ----------------------------------------------------------------------
# 3. Derived observables (dynamic height + freshwater content)
# ----------------------------------------------------------------------
print("3. Computing dynamic height and freshwater content ...")
data_points_csv = os.path.join(OUT, "data_points.csv")
compute_dynamic_height(merged_csv, data_points_csv, verbose=False)
compute_freshwater(merged_csv, os.path.join(OUT, "freshwater_points.csv"), verbose=False)


# ----------------------------------------------------------------------
# 4. Generate a coarse polar grid
# ----------------------------------------------------------------------
print("4. Generating grid ...")
grid_csv = os.path.join(OUT, "grid.csv")
generate_arctic_grid(grid_csv, dx=150_000, extent_m=1_800_000, lat_min=74, lat_max=88)


# ----------------------------------------------------------------------
# 5. Synthetic bathymetry -> attach depth to the grid
#    (a tiny stand-in for the real 548 MB IBCAO NetCDF)
# ----------------------------------------------------------------------
def make_synthetic_ibcao(path):
    import netCDF4 as nc
    from pyproj import Proj, Transformer

    to_polar = Transformer.from_proj(
        Proj(proj="latlong", datum="WGS84"), Proj("EPSG:3413"), always_xy=True
    )
    lons = np.linspace(-40, 40, 40)
    lats = np.linspace(72, 88, 40)
    xs, _ = to_polar.transform(lons, np.full_like(lons, 80.0))
    _, ys = to_polar.transform(np.full_like(lats, 0.0), lats)

    ds = nc.Dataset(path, "w", format="NETCDF4")
    ds.createDimension("x", len(xs))
    ds.createDimension("y", len(ys))
    ds.createVariable("x", "f8", ("x",))[:] = np.sort(xs)
    ds.createVariable("y", "f8", ("y",))[:] = np.sort(ys)
    # smoothly varying ocean depth 500-3500 m (negative = below sea level)
    zz = -(500.0 + 3000.0 * RNG.random((len(ys), len(xs))))
    ds.createVariable("z", "f8", ("y", "x"))[:] = np.reshape(zz, (len(ys), len(xs)))
    ds.close()


print("5. Building synthetic bathymetry and attaching depth ...")
ibcao_nc = os.path.join(OUT, "synthetic_ibcao.nc")
make_synthetic_ibcao(ibcao_nc)
# Attach depth to BOTH the grid and the observations. The objective
# mapping's potential-vorticity term uses bathymetry at the observation
# points as well as the grid points, so the data points need a Depth
# column too (compute_dynamic_height leaves it empty unless given one).
add_depth_to_grid(grid_csv, grid_csv, nc_file=ibcao_nc)
add_depth_to_grid(data_points_csv, data_points_csv, nc_file=ibcao_nc)


# ----------------------------------------------------------------------
# 6. Objective mapping
# ----------------------------------------------------------------------
print("6. Objective mapping ...")
mapped_csv = os.path.join(OUT, "mapped.csv")
objective_map(
    data_csv=data_points_csv,
    grid_csv=grid_csv,
    output_csv=mapped_csv,
    target_time="2013-06-01",
    observable="Surf_DH",
    verbose=False,
)


# ----------------------------------------------------------------------
# 7. Plot observed vs. mapped dynamic height (plain matplotlib scatter)
# ----------------------------------------------------------------------
print("7. Plotting ...")
try:
    import matplotlib
    matplotlib.use("Agg")  # headless-safe
    import matplotlib.pyplot as plt

    obs = pd.read_csv(data_points_csv)
    grd = pd.read_csv(mapped_csv).dropna(subset=["Surf_DH"])

    vmin = float(np.nanmin(obs["Surf_DH"]))
    vmax = float(np.nanmax(obs["Surf_DH"]))

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharex=True, sharey=True)
    sc = axes[0].scatter(obs["Longitude"], obs["Latitude"], c=obs["Surf_DH"],
                         cmap="YlGnBu", vmin=vmin, vmax=vmax, s=25)
    axes[0].set_title("Observed surface DH (synthetic)")
    axes[1].scatter(grd["Longitude"], grd["Latitude"], c=grd["Surf_DH"],
                    cmap="YlGnBu", vmin=vmin, vmax=vmax, s=60, marker="s")
    axes[1].set_title("Objectively mapped DH")
    for ax in axes:
        ax.set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    fig.colorbar(sc, ax=axes, label="Dynamic height (m)", shrink=0.8)

    fig_path = os.path.join(OUT, "tutorial_dh.png")
    fig.savefig(fig_path, dpi=120, bbox_inches="tight")
    print(f"   saved figure -> {fig_path}")
except ImportError:
    print("   matplotlib not installed; skipping plot "
          "(install with: pip install matplotlib)")

print("\nDone. All outputs are under examples/output/ (git-ignored).")
