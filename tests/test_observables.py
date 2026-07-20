import numpy as np
import pandas as pd

from pyoceanmap.observables import compute_dynamic_height, compute_freshwater


def test_compute_dynamic_height_on_synthetic_profiles(synthetic_profiles_csv, tmp_path):
    out = tmp_path / "dh.csv"

    df = compute_dynamic_height(
        input_csv=synthetic_profiles_csv,
        output_csv=str(out),
        max_depth=60,
        dz=10,
        verbose=False,
    )

    assert out.exists()
    assert len(df) == 3  # one row per synthetic station
    assert {"Latitude", "Longitude", "Datetime", "Surf_DH"}.issubset(df.columns)
    assert np.isfinite(df["Surf_DH"]).all()


def test_compute_dynamic_height_skips_shallow_profiles(tmp_path):
    # only 3 depth levels and max depth 20m, below the required max_depth of 60
    rows = [
        {"Datetime": "2013-01-01", "Latitude": 75.0, "Longitude": 10.0,
         "Pressure": d, "Depth": d, "Temperature": -1.0, "Salinity": 34.0}
        for d in (0, 10, 20)
    ]
    input_csv = tmp_path / "shallow.csv"
    pd.DataFrame(rows).to_csv(input_csv, index=False)

    out = tmp_path / "dh.csv"
    df = compute_dynamic_height(str(input_csv), str(out), max_depth=60, dz=10, verbose=False)

    assert len(df) == 0


def test_compute_freshwater_on_synthetic_profiles(synthetic_profiles_csv, tmp_path):
    out = tmp_path / "fw.csv"

    df = compute_freshwater(
        input_csv=synthetic_profiles_csv,
        output_csv=str(out),
        max_depth=60,
        dz=10,
        verbose=False,
    )

    assert out.exists()
    assert len(df) == 3
    assert {"Latitude", "Longitude", "Datetime", "D_Siso", "hFW"}.issubset(df.columns)
    assert np.isfinite(df["hFW"]).all()
    assert np.isfinite(df["D_Siso"]).all()
