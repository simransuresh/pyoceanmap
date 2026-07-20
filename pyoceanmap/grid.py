import numpy as np
import pandas as pd
from pyproj import Proj, Transformer


def generate_arctic_grid(
    output_file,
    dx=50000,
    extent_m=3_000_000,
    lat_min=70,
    lat_max=90,
    lon_min=-180,
    lon_max=180,
    lat_0=90,
    lon_0=0,
    projection="laea"
):
    """
    Generate a projected polar grid and save to CSV.

    Defaults are centered on the Arctic (lat_0=90, lat_min=70), but any
    polar or mid-latitude region can be gridded by overriding lat_0/lon_0
    and the lat/lon bounds (e.g. lat_0=-90 for an Antarctic/Southern Ocean grid).

    Parameters
    ----------
    output_file : str
        Output CSV file
    dx : float
        Grid spacing in meters
    extent_m : float
        Half-width of grid in projected coordinates (meters)
    lat_min, lat_max : float
        Latitude bounds for filtering
    lon_min, lon_max : float
        Longitude bounds for filtering
    lat_0, lon_0 : float
        Projection center
    projection : str
        Projection type ('laea', 'stere', etc.)

    Returns
    -------
    str
        Path to the saved grid CSV file.
    """

    # ------------------------------------------------
    # Define projection
    # ------------------------------------------------
    proj_xy = Proj(proj=projection, lat_0=lat_0, lon_0=lon_0)
    proj_ll = Proj(proj="latlong", datum="WGS84")

    transformer = Transformer.from_proj(proj_xy, proj_ll, always_xy=True)

    # ------------------------------------------------
    # Create grid in projected space
    # ------------------------------------------------
    x = np.arange(-extent_m, extent_m, dx)
    y = np.arange(-extent_m, extent_m, dx)

    X, Y = np.meshgrid(x, y)

    # ------------------------------------------------
    # Convert to lat/lon
    # ------------------------------------------------
    lon, lat = transformer.transform(X, Y)

    # ------------------------------------------------
    # Build dataframe
    # ------------------------------------------------
    df = pd.DataFrame({
        "X_m": X.ravel(),
        "Y_m": Y.ravel(),
        "Longitude": lon.ravel(),
        "Latitude": lat.ravel()
    })

    # ------------------------------------------------
    # Filter valid region
    # ------------------------------------------------
    df = df[
        (df["Latitude"] >= lat_min) &
        (df["Latitude"] <= lat_max) &
        (df["Longitude"] >= lon_min) &
        (df["Longitude"] <= lon_max) &
        (np.isfinite(df["Latitude"])) &
        (np.isfinite(df["Longitude"]))
    ]

    # ------------------------------------------------
    # Save
    # ------------------------------------------------
    df.to_csv(output_file, index=False)

    print(f"Grid saved → {output_file}")
    print(f"Grid points → {len(df)}")

    return output_file