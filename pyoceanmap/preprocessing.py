import os
import glob
import pandas as pd


def merge_txt_to_csv(input_folder, output_file):
    """
    Merge multiple whitespace-delimited TXT hydrographic files into one CSV.

    Parameters
    ----------
    input_folder : str
        Folder containing .txt files.
    output_file : str
        Output merged CSV file.

    Returns
    -------
    str
        Path to saved CSV file.
    """

    files = sorted(glob.glob(os.path.join(input_folder, "*.txt")))

    if len(files) == 0:
        raise FileNotFoundError(f"No .txt files found in {input_folder}")

    df_list = []

    for file in files:
        print(f"Reading: {file}")

        try:
            df = pd.read_csv(
                file,
                sep=r"\s+",
                engine="python",
                on_bad_lines="skip"
            )

            # check datetime column
            if "yyyy-mm-ddThh:mm" not in df.columns:
                print(f"Skipping file (no datetime column): {file}")
                continue

            df["Datetime"] = df["yyyy-mm-ddThh:mm"].astype(str)

            # rename columns safely
            df = df.rename(columns={
                "Longitude_[deg]": "Longitude",
                "Latitude_[deg]": "Latitude",
                "Pressure_[dbar]": "Pressure",
                "Depth_[m]": "Depth",
                "Temp_[°C]": "Temperature",
                "Salinity_[psu]": "Salinity"
            })

            required_cols = [
                "Datetime", "Latitude", "Longitude",
                "Pressure", "Depth", "Temperature", "Salinity"
            ]

            df = df[[col for col in required_cols if col in df.columns]]

            df_list.append(df)

        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue

    if len(df_list) == 0:
        raise ValueError("No valid files could be read.")

    merged_df = pd.concat(df_list, ignore_index=True)

    # fix invalid times
    merged_df["Datetime"] = merged_df["Datetime"].str.replace("99:99", "00:00")

    merged_df.to_csv(output_file, index=False)

    print(f"Merged file saved → {output_file}")
    print(f"Total rows: {len(merged_df)}")

    return output_file