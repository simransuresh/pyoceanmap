import numpy as np
import pandas as pd

from pyoceanmap.mapping import objective_map


def test_objective_map_end_to_end(tiny_data_points_csv, tiny_grid_csv, tmp_path):
    out = tmp_path / "mapped.csv"

    df = objective_map(
        data_csv=tiny_data_points_csv,
        grid_csv=tiny_grid_csv,
        output_csv=str(out),
        target_time="2013-02-01",
        observable="Surf_DH",
        L1=600,
        L2=300,
        verbose=False,
    )

    assert out.exists()
    assert {"Latitude", "Longitude", "Surf_DH", "Surf_DH_err"}.issubset(df.columns)

    # grid points close to observation stations should get a finite mapped value
    near = df[df["Latitude"] < 79]
    assert np.isfinite(near["Surf_DH"]).any()

    # the grid point far from any station (40, -100) should have no neighbors within L1
    far = df[(df["Latitude"] == 40.0) & (df["Longitude"] == -100.0)]
    assert len(far) == 1
    assert np.isnan(far["Surf_DH"].iloc[0])


def test_objective_map_grid_with_high_precision_coords(tiny_data_points_csv, tmp_path):
    """
    Regression test: grid coordinates from a map projection carry full
    floating-point precision. The PV depth lookup rounds to 5 decimals, so
    build_depth_info must round its keys too -- otherwise grid-point depths
    resolve to NaN and every multi-neighbour grid point maps to NaN.
    """
    # A cluster of grid points among the observation stations, but with many
    # decimal places (as a real projected grid would have).
    grid = pd.DataFrame({
        "Latitude": [75.123456789, 75.987654321, 76.111111111, 76.500000123],
        "Longitude": [10.123456789, 15.987654321, 17.111111111, 12.500000123],
        "Depth": [200.0, 210.0, 220.0, 205.0],
    })
    grid_csv = tmp_path / "hp_grid.csv"
    grid.to_csv(grid_csv, index=False)

    out = tmp_path / "mapped_hp.csv"
    df = objective_map(
        data_csv=tiny_data_points_csv,
        grid_csv=str(grid_csv),
        output_csv=str(out),
        target_time="2013-02-01",
        observable="Surf_DH",
        verbose=False,
    )

    # With several observation stations within range, at least one
    # high-precision grid point must receive a finite mapped value.
    assert np.isfinite(df["Surf_DH"]).any()
