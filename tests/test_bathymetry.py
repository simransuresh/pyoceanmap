import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from pyoceanmap.bathymetry import nearest_depth, add_depth_to_grid


def test_nearest_depth_returns_closest_point_value():
    points = np.array([[0.0, 0.0], [1.0, 1.0], [5.0, 5.0]])
    depth_flat = np.array([10.0, 20.0, 30.0])
    tree = cKDTree(points)

    depth = nearest_depth(0.1, 0.1, tree, depth_flat)
    assert depth == 10.0

    depth_km = nearest_depth(0.1, 0.1, tree, depth_flat, return_km=True)
    assert depth_km == 0.01


def test_nearest_depth_nan_passthrough():
    points = np.array([[0.0, 0.0]])
    depth_flat = np.array([np.nan])
    tree = cKDTree(points)

    assert np.isnan(nearest_depth(0.0, 0.0, tree, depth_flat))


def test_add_depth_to_grid_end_to_end(tiny_ibcao_nc, tiny_grid_csv, tmp_path):
    out = tmp_path / "grid_with_depth.csv"

    result = add_depth_to_grid(
        grid_csv=tiny_grid_csv,
        output_csv=str(out),
        nc_file=tiny_ibcao_nc,
        delete_after=False,
    )

    assert isinstance(result, pd.DataFrame)
    assert out.exists()

    df = pd.read_csv(out)
    assert "Depth" in df.columns
    assert len(df) == len(pd.read_csv(tiny_grid_csv))
    # synthetic IBCAO fixture is uniformly -200 m (ocean) everywhere
    assert np.allclose(df["Depth"].dropna(), 200.0)
