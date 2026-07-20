import numpy as np
import pandas as pd
from scipy import interpolate
import gsw

from .utils import get_g


# --------------------------------------------------
# Dynamic Height
# --------------------------------------------------
def compute_dynamic_height(
    input_csv,
    output_csv="data_points.csv",
    max_depth=400,
    dz=2,
    depth_func=None,
    verbose=True
):
    """
    Compute surface dynamic height (SSH proxy) from hydrographic profiles.
    """

    df = pd.read_csv(input_csv)
    df["Datetime"] = pd.to_datetime(df["Datetime"])

    # consistent grouping
    df["lat"] = df["Latitude"].round(5)
    df["lon"] = df["Longitude"].round(5)

    grouped = df.groupby(["lat", "lon"])

    z = np.arange(0, max_depth + dz, dz)

    results = []

    if verbose:
        print("Computing dynamic height...")

    for i, ((lat, lon), g) in enumerate(grouped):

        g = g.sort_values("Depth")

        depth = g["Depth"].values
        temp  = g["Temperature"].values
        sal   = g["Salinity"].values
        pres  = g["Pressure"].values

        # skip shallow or sparse profiles
        if len(depth) < 5 or np.nanmax(depth) < max_depth:
            continue

        mask = depth <= max_depth
        depth, temp, sal, pres = depth[mask], temp[mask], sal[mask], pres[mask]

        if len(depth) < 5:
            continue

        try:
            # interpolate
            Tz = interpolate.interp1d(depth, temp, bounds_error=False, fill_value="extrapolate")(z)
            Sz = interpolate.interp1d(depth, sal,  bounds_error=False, fill_value="extrapolate")(z)
            Pz = interpolate.interp1d(depth, pres, bounds_error=False, fill_value="extrapolate")(z)

            # TEOS-10
            SA = gsw.SA_from_SP(Sz, Pz, lon, lat)
            CT = gsw.CT_from_t(SA, Tz, Pz)

            dyn = gsw.geostrophy.geo_strf_dyn_height(SA, CT, Pz, p_ref=max_depth)
            ssh = float(dyn[0] / get_g(lat))

            # optional bathymetry
            bathy = depth_func(lat, lon) if depth_func else np.nan

            results.append({
                "Latitude": lat,
                "Longitude": lon,
                "Depth": bathy,
                "Datetime": g["Datetime"].iloc[0],
                "Surf_DH": round(ssh, 5)
            })

        except Exception:
            continue

        if verbose and i % 100 == 0:
            print(f"[{i}] processed...")

    out_df = pd.DataFrame(results)
    out_df.to_csv(output_csv, index=False)

    if verbose:
        print(f"Saved {len(out_df)} dynamic height points → {output_csv}")

    return out_df


# --------------------------------------------------
# Freshwater Content
# --------------------------------------------------
def compute_freshwater(
    input_csv,
    output_csv="freshwater_points.csv",
    max_depth=400,
    dz=2,
    Sref=35,
    Siso=34,
    verbose=True
):
    """
    Compute freshwater content (hFW) and isohaline depth (D_Siso).
    """

    df = pd.read_csv(input_csv)
    df["Datetime"] = pd.to_datetime(df["Datetime"])

    df["lat"] = df["Latitude"].round(5)
    df["lon"] = df["Longitude"].round(5)

    grouped = df.groupby(["lat", "lon"])

    z = np.arange(0, max_depth + dz, dz)

    results = []

    if verbose:
        print("Computing freshwater content...")

    for i, ((lat, lon), g) in enumerate(grouped):

        g = g.sort_values("Depth")

        depth = g["Depth"].values
        sal   = g["Salinity"].values

        if len(depth) < 5 or np.nanmax(depth) < max_depth:
            continue

        mask = depth <= max_depth
        depth, sal = depth[mask], sal[mask]

        if len(depth) < 5:
            continue

        try:
            # interpolate salinity
            Sz = interpolate.interp1d(
                depth, sal,
                bounds_error=False,
                fill_value="extrapolate"
            )(z)

            # isohaline depth
            idx = np.abs(Sz - Siso).argmin()
            D_Siso = float(z[idx])

            # freshwater content (vectorized instead of loop)
            dz_array = np.diff(z[:idx+1])
            hfw = np.sum((Sref - Sz[:idx]) * dz_array / Sref)

            results.append({
                "Latitude": lat,
                "Longitude": lon,
                "Datetime": g["Datetime"].iloc[0],
                "D_Siso": round(D_Siso, 2),
                "hFW": round(float(hfw), 5)
            })

        except Exception:
            continue

        if verbose and i % 100 == 0:
            print(f"[{i}] processed...")

    out_df = pd.DataFrame(results)
    out_df.to_csv(output_csv, index=False)

    if verbose:
        print(f"Saved {len(out_df)} freshwater points → {output_csv}")

    return out_df