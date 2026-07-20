import pandas as pd

from pyoceanmap.grid import generate_arctic_grid


def test_generate_arctic_grid_columns_and_bounds(tmp_path):
    out = tmp_path / "grid.csv"

    result = generate_arctic_grid(
        output_file=str(out),
        dx=500_000,
        extent_m=1_500_000,
        lat_min=70,
        lat_max=90,
    )

    assert result == str(out)
    assert out.exists()

    df = pd.read_csv(out)
    assert {"X_m", "Y_m", "Longitude", "Latitude"}.issubset(df.columns)
    assert len(df) > 0
    assert (df["Latitude"] >= 70).all()
    assert (df["Latitude"] <= 90).all()
    assert df["Longitude"].between(-180, 180).all()


def test_generate_arctic_grid_southern_hemisphere_via_lat_0(tmp_path):
    out = tmp_path / "grid_south.csv"

    generate_arctic_grid(
        output_file=str(out),
        dx=500_000,
        extent_m=1_500_000,
        lat_min=-90,
        lat_max=-60,
        lat_0=-90,
    )

    df = pd.read_csv(out)
    assert len(df) > 0
    assert (df["Latitude"] <= -60).all()
