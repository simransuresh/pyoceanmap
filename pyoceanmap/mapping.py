import numpy as np
import pandas as pd
import random

from .utils import (
    D_mat, PV_mat, tdiff, signal, noise, covar1, covar2, get_seas
)


# --------------------------------------------------
# Build depth lookup
# --------------------------------------------------
def build_depth_info(data_csv, grid_csv):
    """
    Build a (Latitude, Longitude) -> {"depth": ...} lookup used for the
    potential-vorticity terms in :func:`objective_map`.

    Parameters
    ----------
    data_csv : str
        CSV of observation points with Latitude, Longitude, Depth columns.
    grid_csv : str
        CSV of target grid points with Latitude, Longitude, Depth columns.

    Returns
    -------
    dict
        Mapping from (Latitude, Longitude) to {"depth": float}.
    """
    df = pd.concat([pd.read_csv(data_csv), pd.read_csv(grid_csv)])

    return {
        (row["Latitude"], row["Longitude"]): {"depth": row["Depth"]}
        for _, row in df.iterrows()
    }


# --------------------------------------------------
# Objective Mapping
# --------------------------------------------------
def objective_map(
    data_csv,
    grid_csv,
    output_csv,
    target_time,
    observable,
    L1=600, phi1=1,
    L2=300, phi2=0.4,
    T=60,
    depth_info=None,
    verbose=True
):
    """
    Map irregularly distributed ocean observations onto a grid using a
    two-stage, physics-informed objective mapping (optimal interpolation)
    scheme.

    Stage 1 uses a coarse spatial/potential-vorticity covariance (L1, phi1)
    to remove large-scale structure; stage 2 re-maps the stage-1 residuals
    with a finer spatial/potential-vorticity/temporal covariance (L2, phi2,
    T) to capture smaller-scale, time-varying structure. The two stages are
    summed for the final mapped value.

    Parameters
    ----------
    data_csv : str
        CSV of observation points. Must contain Latitude, Longitude, Depth,
        Datetime, and the ``observable`` column.
    grid_csv : str
        CSV of target grid points. Must contain Latitude, Longitude, Depth.
    output_csv : str
        Path to write the mapped field to.
    target_time : str or datetime-like
        Time to map the field to (used for temporal decorrelation and
        seasonal filtering of candidate observations).
    observable : str
        Name of the column in ``data_csv`` to map (e.g. "Surf_DH").
    L1, phi1 : float
        Stage 1 spatial decorrelation length scale (km) and
        potential-vorticity decorrelation scale.
    L2, phi2, T : float
        Stage 2 spatial, potential-vorticity, and temporal (days)
        decorrelation scales.
    depth_info : dict, optional
        Precomputed (Latitude, Longitude) -> {"depth": ...} lookup. If not
        given, it is built from ``data_csv`` and ``grid_csv`` via
        :func:`build_depth_info`.
    verbose : bool
        Whether to print progress.

    Returns
    -------
    pandas.DataFrame
        One row per grid point, with the mapped ``observable`` value and a
        ``{observable}_err`` mapping-error column. Grid points with no
        observations within ``L1`` km and 3 years of ``target_time`` are
        returned as NaN.
    """

    # -----------------------------
    # Depth lookup
    # -----------------------------
    if depth_info is None:
        depth_info = build_depth_info(data_csv, grid_csv)

    # -----------------------------
    # Load observations
    # -----------------------------
    dp = pd.read_csv(data_csv)
    dp = dp.dropna(subset=["Datetime", observable])
    dp["Datetime"] = pd.to_datetime(dp["Datetime"])

    hydr_data = {
        (row["Latitude"], row["Longitude"]): {
            "depth": row["Depth"],
            "dt": row["Datetime"],
            "val": float(row[observable])
        }
        for _, row in dp.iterrows()
    }

    # -----------------------------
    # Outlier removal
    # -----------------------------
    vals = np.array([v["val"] for v in hydr_data.values()])
    mean, std = np.nanmean(vals), np.nanstd(vals)

    hydr_data = {
        k: v for k, v in hydr_data.items()
        if abs(v["val"] - mean) < 2 * std
    }

    # -----------------------------
    # Weight function
    # -----------------------------
    def find_weights(subset, latg, long, tg=None):

        D = D_mat(subset, target=(latg, long))

        PV = PV_mat(
            [ll[0] for ll in subset],
            [ll[1] for ll in subset],
            latg, long,
            depth_info
        )[:, 0]

        w = (D / L1) ** 2 + (PV / phi1) ** 2

        if tg is not None:
            tvals = [hydr_data[ll]["dt"] for ll in subset]
            w += (tdiff(tvals, tg) / T) ** 2

        w = np.exp(-w)
        return {ll: w[i] for i, ll in enumerate(subset)}

    # -----------------------------
    # Core mapping per grid point
    # -----------------------------
    def map_point(latg, long, tg):

        subset = [
            ll for ll, v in hydr_data.items()
            if D_mat(ll, target=(latg, long)) <= L1
            and tdiff(v["dt"], tg) <= 1095
            and v["dt"].month in get_seas(tg.month)
        ]

        if len(subset) == 0:
            return np.nan, np.nan

        # Subsampling for efficiency
        if len(subset) > 60:
            subset_rand = random.sample(subset, 20)

            w1 = find_weights(subset, latg, long)
            subset_w1 = sorted(w1, key=w1.get, reverse=True)[:20]

            w2 = find_weights(subset, latg, long, tg)
            subset_w2 = sorted(w2, key=w2.get, reverse=True)[:20]

            subset = list(set(subset_rand + subset_w1 + subset_w2))

        Od = np.array([hydr_data[ll]["val"] for ll in subset])

        if len(Od) < 2:
            return (Od[0], np.nan) if len(Od) == 1 else (np.nan, np.nan)

        # Distance & PV matrices
        D_dd = D_mat(subset)
        D_dg = D_mat(subset, target=(latg, long))

        lats = [ll[0] for ll in subset]
        lons = [ll[1] for ll in subset]

        PV_dd = PV_mat(lats, lons, lats, lons, depth_info)
        PV_dg = PV_mat(lats, lons, latg, long, depth_info)[:, 0]

        # -----------------
        # Stage 1
        # -----------------
        sig = signal(Od, len(Od))
        noise_var = noise(subset, Od, len(Od))

        Cdd = covar1(D_dd, PV_dd, sig, L1, phi1)
        Cdg = covar1(D_dg, PV_dg, sig, L1, phi1)

        Cdd += noise_var * np.eye(len(Od))
        invCdd = np.linalg.inv(Cdd)

        m = np.linalg.solve(Cdd, Od - np.mean(Od))
        Og1 = float(np.dot(Cdg.T, m) + np.mean(Od))

        # Error stage 1
        err1_sq = sig - np.dot(Cdg.T, np.dot(invCdd, Cdg))
        err1_sq = float(np.maximum(err1_sq, 0))
        Og1_err = np.sqrt(err1_sq)

        # -----------------
        # Stage 2
        # -----------------
        Od2 = Od - Og1

        sig2 = signal(Od2, len(Od2))
        noise_var2 = noise(subset, Od2, len(Od2))

        tvals = [hydr_data[ll]["dt"] for ll in subset]

        Cdd2 = covar2(D_dd, PV_dd, tdiff(tvals), sig2, L2, phi2, T)
        Cdg2 = covar2(D_dg, PV_dg, tdiff(tvals, tg), sig2, L2, phi2, T)

        Cdd2 += noise_var2 * np.eye(len(Od2))
        invCdd2 = np.linalg.inv(Cdd2)

        m2 = np.linalg.solve(Cdd2, Od2 - np.mean(Od2))
        Og2 = float(np.dot(Cdg2.T, m2) + np.mean(Od2))

        # Error stage 2
        err2_sq = sig2 - np.dot(Cdg2.T, np.dot(invCdd2, Cdg2))
        err2_sq = float(np.maximum(err2_sq, 0))
        Og2_err = np.sqrt(err2_sq)

        # Final result
        Og = Og1 + Og2
        Og_err = Og2_err  # standard choice

        return Og, Og_err

    # -----------------------------
    # Apply to grid
    # -----------------------------
    gp = pd.read_csv(grid_csv)
    tg = pd.to_datetime(target_time)

    results = []

    for i, row in gp.iterrows():
        lat, lon = row["Latitude"], row["Longitude"]

        val, err = map_point(lat, lon, tg)

        results.append({
            "Latitude": lat,
            "Longitude": lon,
            "Depth": row["Depth"],
            "Datetime": tg,
            observable: val,
            f"{observable}_err": err
        })

        if verbose and i % 50 == 0:
            print(f"[{i}/{len(gp)}] mapped...")

    out_df = pd.DataFrame(results)
    out_df.to_csv(output_csv, index=False)

    if verbose:
        print(f"Saved mapped field → {output_csv}")

    return out_df
