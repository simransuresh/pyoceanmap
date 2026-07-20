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
