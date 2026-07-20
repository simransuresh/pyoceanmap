import numpy as np
import pandas as pd
import pytest


# Three Arctic-ish stations, each with a short vertical profile.
# Values are physically plausible (Arctic surface halocline) but small
# enough to keep max_depth/dz tiny so tests stay fast.
STATIONS = [
    {"lat": 75.00000, "lon": 10.00000},
    {"lat": 76.00000, "lon": 15.00000},
    {"lat": 77.00000, "lon": 20.00000},
]
DEPTHS = [0, 10, 20, 30, 40, 50, 60]


def _profile_rows(lat, lon, datetime_str):
    rows = []
    for i, depth in enumerate(DEPTHS):
        rows.append({
            "Datetime": datetime_str,
            "Latitude": lat,
            "Longitude": lon,
            "Pressure": float(depth),
            "Depth": float(depth),
            "Temperature": -1.0 + 0.02 * depth,
            "Salinity": 33.0 + 0.03 * depth,
        })
    return rows


@pytest.fixture
def synthetic_profiles_csv(tmp_path):
    rows = []
    for i, st in enumerate(STATIONS):
        rows += _profile_rows(st["lat"], st["lon"], f"2013-0{i + 1}-01T00:00")
    df = pd.DataFrame(rows)
    path = tmp_path / "merged.csv"
    df.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def synthetic_txt_dir(tmp_path):
    data_dir = tmp_path / "txt_data"
    data_dir.mkdir()

    header = "yyyy-mm-ddThh:mm Latitude_[deg] Longitude_[deg] Pressure_[dbar] Depth_[m] Temp_[°C] Salinity_[psu]"

    lines_2011 = [header]
    for depth in DEPTHS:
        lines_2011.append(
            f"2011-01-18T04:32 {75.0:.4f} {10.0:.4f} {float(depth):.1f} {float(depth):.2f} {(-1.0 + 0.02*depth):.3f} {(33.0 + 0.03*depth):.4f}"
        )
    # one row with a missing/placeholder time (99:99) to exercise the fix-up logic
    lines_2011.append(f"2011-01-19T99:99 {75.5:.4f} {10.5:.4f} 5.0 4.95 -0.9 33.1")

    (data_dir / "ArcticOcean_phys_oce_2011.txt").write_text("\n".join(lines_2011) + "\n")

    return str(data_dir)


@pytest.fixture
def tiny_grid_csv(tmp_path):
    rows = []
    for st in STATIONS:
        rows.append({"Latitude": st["lat"], "Longitude": st["lon"], "Depth": 200.0})
    # one grid point far from any observation, to exercise the "no neighbors" path
    rows.append({"Latitude": 40.0, "Longitude": -100.0, "Depth": 200.0})
    df = pd.DataFrame(rows)
    path = tmp_path / "grid.csv"
    df.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def tiny_data_points_csv(tmp_path):
    rows = []
    for i, st in enumerate(STATIONS):
        rows.append({
            "Latitude": st["lat"],
            "Longitude": st["lon"],
            "Depth": 200.0,
            "Datetime": f"2013-0{i + 1}-01",
            "Surf_DH": 0.1 + 0.01 * i,
        })
    df = pd.DataFrame(rows)
    path = tmp_path / "data_points.csv"
    df.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def tiny_ibcao_nc(tmp_path):
    nc = pytest.importorskip("netCDF4")
    from pyproj import Proj, Transformer

    path = tmp_path / "tiny_ibcao.nc"

    # Build a small stereographic grid covering the STATIONS' lat/lon range,
    # all with negative z (ocean) so nearest_depth returns finite values.
    proj_polar = Proj("EPSG:3413")
    proj_ll = Proj(proj="latlong", datum="WGS84")
    to_polar = Transformer.from_proj(proj_ll, proj_polar, always_xy=True)

    lons = np.linspace(5, 25, 12)
    lats = np.linspace(70, 80, 12)
    xs, ys = to_polar.transform(lons, lats)

    ds = nc.Dataset(str(path), "w", format="NETCDF4")
    ds.createDimension("x", len(xs))
    ds.createDimension("y", len(ys))
    xvar = ds.createVariable("x", "f8", ("x",))
    yvar = ds.createVariable("y", "f8", ("y",))
    zvar = ds.createVariable("z", "f8", ("y", "x"))

    xvar[:] = np.sort(xs)
    yvar[:] = np.sort(ys)
    zvar[:, :] = np.full((len(ys), len(xs)), -200.0)  # uniform 200 m ocean depth everywhere
    ds.close()

    return str(path)
