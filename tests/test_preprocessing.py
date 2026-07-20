import pytest

from pyoceanmap.preprocessing import merge_txt_to_csv


def test_merge_txt_to_csv_produces_expected_columns(synthetic_txt_dir, tmp_path):
    out = tmp_path / "merged.csv"
    result = merge_txt_to_csv(synthetic_txt_dir, str(out))

    assert result == str(out)
    assert out.exists()

    import pandas as pd
    df = pd.read_csv(out)

    expected_cols = {"Datetime", "Latitude", "Longitude", "Pressure", "Depth", "Temperature", "Salinity"}
    assert expected_cols.issubset(df.columns)
    assert len(df) > 0
    # the placeholder "99:99" time must have been rewritten
    assert not df["Datetime"].str.contains("99:99").any()


def test_merge_txt_to_csv_raises_on_empty_folder(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(FileNotFoundError):
        merge_txt_to_csv(str(empty_dir), str(tmp_path / "out.csv"))
