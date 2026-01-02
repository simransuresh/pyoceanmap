import pandas as pd

dp = pd.read_csv('../data_preparation/data_points.csv')
dp_depth = {
    (row['Latitude'], row['Longitude']): {
        'depth': row['Depth'],
    }
    for _, row in dp.iterrows()
}

gp = pd.read_csv('../grid_setup/grid_50km_nplaea.csv')
gp_depth = {
    (row['Latitude'], row['Longitude']): {
        'depth': row['Depth'],
    }
    for _, row in gp.iterrows()
}

depth_info = dp_depth | gp_depth

