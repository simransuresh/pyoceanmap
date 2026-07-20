import os
import numpy as np
import netCDF4 as nc
import pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer
import urllib.request
import tempfile

# ----------------------------------------------------
# Download IBCAO (if needed)
# ----------------------------------------------------
def download_ibcao(url, save_path):
    print("Downloading IBCAO dataset...")
    urllib.request.urlretrieve(url, save_path)
    print("Download complete:", save_path)
    return save_path


# ----------------------------------------------------
# Load IBCAO + build KDTree
# ----------------------------------------------------
def load_ibcao(nc_file):
    print("Loading IBCAO bathymetry...")

    ds = nc.Dataset(nc_file, "r")

    x = ds.variables["x"][:]
    y = ds.variables["y"][:]
    z = ds.variables["z"][:]

    ds.close()

    # Convert to positive ocean depth
    z = np.where(z < 0, -z, np.nan)

    # Convert projection → lat/lon
    transformer = Transformer.from_crs(
        "EPSG:3413", "EPSG:4326", always_xy=True
    )

    xx, yy = np.meshgrid(x, y)
    lon, lat = transformer.transform(xx, yy)

    # KDTree
    points = np.column_stack((lat.ravel(), lon.ravel()))
    tree = cKDTree(points)

    depth_flat = z.ravel()

    print("KDTree ready.")
    return tree, depth_flat


# ----------------------------------------------------
# Query depth
# ----------------------------------------------------
def nearest_depth(lat, lon, tree, depth_flat, return_km=False):
    """
    Get nearest IBCAO depth at given lat/lon.
    """
    _, idx = tree.query([lat, lon])
    depth = depth_flat[idx]

    if np.isnan(depth):
        return np.nan

    return depth / 1000 if return_km else depth

# ----------------------------------------------------
# Add depth to grid (FULL PIPELINE)
# ----------------------------------------------------
def add_depth_to_grid(
    grid_csv,
    output_csv,
    ibcao_url=None,
    nc_file=None,
    delete_after=True
):
    """
    Add bathymetric depth to grid points.

    Parameters
    ----------
    grid_csv : str
        Input grid file (must contain Latitude, Longitude)
    output_csv : str
        Output file with depth column
    ibcao_url : str (optional)
        URL to download IBCAO file
    nc_file : str (optional)
        Local IBCAO file path
    delete_after : bool
        Delete downloaded file after processing
    """

    # ------------------------------------------------
    # Handle file input
    # ------------------------------------------------
    if nc_file is None:
        if ibcao_url is None:
            raise ValueError("Provide either nc_file or ibcao_url")

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".nc")
        nc_file = tmp_file.name
        download_ibcao(ibcao_url, nc_file)

        downloaded = True
    else:
        downloaded = False

    # ------------------------------------------------
    # Load bathymetry
    # ------------------------------------------------
    tree, depth_flat = load_ibcao(nc_file)

    # ------------------------------------------------
    # Apply to grid
    # ------------------------------------------------
    df = pd.read_csv(grid_csv)

    df["Depth"] = [
        nearest_depth(lat, lon, tree, depth_flat)
        for lat, lon in zip(df["Latitude"], df["Longitude"])
    ]

    df.to_csv(output_csv, index=False)

    print("Saved grid with depth →", output_csv)

    # ------------------------------------------------
    # Cleanup
    # ------------------------------------------------
    if downloaded and delete_after:
        os.remove(nc_file)
        print("Temporary IBCAO file deleted.")

    return df