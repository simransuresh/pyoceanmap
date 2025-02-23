import csv
import numpy as np
from scipy.spatial import cKDTree
import pandas as pd
import netCDF4 as nc
from pyproj import Proj, transform, Transformer
import matplotlib.pyplot as plt
import itertools
import cartopy.crs as ccrs

# print('Loading bathy file...')
# ds = nc.Dataset('./data/IBCAO_v4_2_13_400m_ice.nc', 'r')
# x = ds.variables['x'][:]
# y = ds.variables['y'][:]
# z = ds.variables['z'][:]    # in meters
# ds.close()

# print('Forming NP stereo lat lon...')
# proj_polar = Proj(proj='stere', lat_ts=60, lon_0=0, lat_0=90, ellps='WGS84')
# proj_wgs84 = Proj(proj='latlong', ellps='WGS84')

# transformer = Transformer.from_proj(proj_polar, proj_wgs84)
# xx, yy = np.meshgrid(x, y)
# lon, lat = transformer.transform(xx, yy)
# # print(lon)

# print('Forming tree to query nn of each lat lon.')
# # form a KD tree which gives nearest depth z to a lat, lon
# points = np.column_stack((lat.flatten(), lon.flatten()))
# tree = cKDTree(points)

# # finding closest depth to a grid point (negate depth as it is already negative or else sqrt(neg) in PV function will give err)
# def nearest_depth(target_lat, target_lon):
#     _, idx = tree.query([target_lat, target_lon])
#     return -z.flatten()[idx]/1000 # in km

# print('get all lat lon of data point and grid together..')
# ll = list(hydr_data.keys())
# lats = np.linspace(60, 90, 121)
# lons = np.linspace(-179.25, 180, 480)
# comb = np.concatenate((np.array(list(itertools.product(lats, lons))), np.array(ll)))
# print(len(comb))

# write into depths.csv - gves nn depth of all data points unfiltered and grid points

# depths_500m.csv - all data and grid points with depth>500m

# data_points.csv - all data points within CAO with dh assigned from hydr_data

# grid_points.csv - all grid points within CAO
 
print('get hydr profiles...')
hydr_data = {}
# Open and read the CSV file
with open('results/dh_2011_2018_deep.csv', mode='r') as file:    # Max, Min: 1.9064679533773496 -0.3754665568686381
    reader = csv.DictReader(file)

    # Iterate over each row in the CSV
    for row in reader:
            # Store the datetime and dynamic height in the dict with the key (lat, lon)
            hydr_data[(float(row['Latitude']), float(row['Longitude']))] = {
                    'dt': row['Datetime'], 'dh': float(row['Dynamic_height']) 
                    if row['Dynamic_height']!='' 
                    else np.nan
            }
            

# Read your CSV into a DataFrame
df = pd.read_csv('results/depth_500m.csv')[24475:]
print(df.head())

# Function to retrieve datetime and ssh from the dictionary
def get_hydr_data(row):
    key = (float(row['Latitude']), float(row['Longitude']))
    if key in hydr_data:
        return hydr_data[key]['dt'], hydr_data[key]['dh']
    else:
        return None, np.nan  # Default values if key is not found

# Apply the function to each row and create new columns
df[['Datetime', 'Dynamic_height']] = df.apply(
    lambda row: pd.Series(get_hydr_data(row)), axis=1
)

# Save the updated DataFrame to a new CSV
df.to_csv('all_500m.csv', index=False)  # take as historic profiles

print(df)



