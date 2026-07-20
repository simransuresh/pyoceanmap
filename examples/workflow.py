"""
Example: Full workflow using pyoceanmap

Steps:
1. Merge TXT hydrographic files → CSV
2. Compute dynamic height (or other observable)
3. Generate LAEA grid (50 km)
4. Add bathymetry (IBCAO)
5. Perform objective mapping for Sept 2013

Run:
    python full_workflow.py
"""

import os

from pyoceanmap import (
    merge_txt_to_csv,
    compute_dynamic_height,
    generate_arctic_grid,
    add_depth_to_grid,
    objective_map
)

# ----------------------------------
# USER INPUT
# ----------------------------------
INPUT_TXT_FOLDER = "../data"           # folder containing .txt files
WORKDIR = "./output"               # working directory
OBSERVABLE = "Surf_DH"             # change later if needed
TARGET_TIME = "2013-09-01"

# IBCAO file (can be auto-downloaded if you implemented it)
IBCAO_FILE = "./IBCAO_400m.nc"

# ----------------------------------
# Create working directory
# ----------------------------------
os.makedirs(WORKDIR, exist_ok=True)

# ----------------------------------
# Step 1: Merge TXT → CSV
# ----------------------------------
print("\n--- STEP 1: Merge TXT files ---")

merged_csv = os.path.join(WORKDIR, "merged_data.csv")

merge_txt_to_csv(
    input_folder=INPUT_TXT_FOLDER,
    output_file=merged_csv
)

# ----------------------------------
# Step 2: Compute Dynamic Height
# ----------------------------------
print("\n--- STEP 2: Compute Dynamic Height ---")

data_points_csv = os.path.join(WORKDIR, "data_points.csv")

compute_dynamic_height(
    input_csv=merged_csv,
    output_csv=data_points_csv
)

# ----------------------------------
# Step 3: Generate 50 km LAEA grid
# ----------------------------------
print("\n--- STEP 3: Generate Grid ---")

grid_csv = os.path.join(WORKDIR, "grid_50km.csv")

generate_arctic_grid(
    output_file=grid_csv,
    dx=50000,          # 50 km
    lat_min=70,
    lat_max=90
)

# ----------------------------------
# Step 4: Add Bathymetry
# ----------------------------------
print("\n--- STEP 4: Add Bathymetry ---")

grid_bathy_csv = os.path.join(WORKDIR, "grid_50km_bathy.csv")

add_depth_to_grid(
    grid_csv=grid_csv,
    output_csv=grid_bathy_csv,
    nc_file=IBCAO_FILE
)

# ----------------------------------
# Step 5: Objective Mapping
# ----------------------------------
print("\n--- STEP 5: Objective Mapping ---")

mapped_output = os.path.join(WORKDIR, "mapped_2013_09.csv")

objective_map(
    data_csv=data_points_csv,
    grid_csv=grid_bathy_csv,
    output_csv=mapped_output,
    target_time=TARGET_TIME,
    observable=OBSERVABLE
)

# ----------------------------------
# DONE
# ----------------------------------
print("\n✅ Workflow complete!")
print(f"Output file: {mapped_output}")