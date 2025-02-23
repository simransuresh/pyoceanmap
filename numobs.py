import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import matplotlib.colors as mcolors

# Load the data points (irregular) and gridded points (regular)
data_points = pd.read_csv("data_500m.csv")  # Columns: lat, lon, dh
gridded_points = pd.read_csv("grid_50km_nplaea.csv")  # Columns: lat, lon

# Convert latitude and longitude to radians (for haversine calculations)
data_coords = np.radians(data_points[['Latitude', 'Longitude']].to_numpy())
grid_coords = np.radians(gridded_points[['Latitude', 'Longitude']].to_numpy())

# Constants for Earth's shape
a = 6378.137  # Equatorial radius (km)
b = 6356.752  # Polar radius (km)
e2 = 1 - (b**2 / a**2)  # Eccentricity squared

# Function to calculate the radius of Earth at a given latitude
def earth_radius(lat_rad):
    sin_lat = np.sin(lat_rad)
    cos_lat = np.cos(lat_rad)
    term1 = (a**2 * cos_lat)**2 / (a**2 * cos_lat**2 + b**2 * sin_lat**2)
    term2 = (b**2 * sin_lat)**2 / (a**2 * cos_lat**2 + b**2 * sin_lat**2)
    return np.sqrt(term1 + term2)

# Build a cKDTree for efficient spatial queries
tree = cKDTree(data_coords)

# Function to count points within radius for each grid point
def count_within_radius(grid_coord):
    lat_rad = grid_coord[0]  # Latitude in radians
    local_radius = earth_radius(lat_rad)  # Adjusted radius based on latitude
    indices = tree.query_ball_point(grid_coord, 600.0 / local_radius)
    return len(indices)

# Compute the count for each gridded point
counts = []
for grid_coord in grid_coords:
    count = count_within_radius(grid_coord)  # Radius set to 600 km
    counts.append(count)

# Add counts to the gridded points dataframe
gridded_points['numobs'] = counts
print(min(counts), max(counts))

# Define custom bins for the color scale
bins = [0, 100, 500, 1000, 3000, 7000]
norm = mcolors.BoundaryNorm(bins, ncolors=256, extend='max')  # Normalize to bins

# Create the Basemap instance for polar stereographic projection
m = Basemap(projection='nplaea', boundinglat=70, lon_0=0, resolution='l', round=True)

# Plot
fig, ax = plt.subplots(figsize=(8, 8))
m.drawcoastlines(linewidth=1.2)
m.drawparallels([80], labels=[True], linewidth=0.5, color='gray', fontsize=6)
m.drawmeridians([-180, -90, 0, 90], labels=[True, True, True, True], linewidth=0.5, color='gray', fontsize=6)

# Map longitude and latitude to the Basemap's x and y
x, y = m(gridded_points['Longitude'], gridded_points['Latitude'])

# Scatter plot with custom bins
sc = m.scatter(x, y, s=30, c=gridded_points['numobs'], cmap='viridis', norm=norm, edgecolor='k', linewidth=0.5)

# Add the colorbar
cbar = plt.colorbar(sc, ax=ax, shrink=0.7, boundaries=bins, ticks=bins)
cbar.set_label("Number of Observations")
cbar.ax.set_yticklabels([f'{bins[i]}-{bins[i+1]}' for i in range(len(bins)-1)] + ['6000+'])

plt.title("Observation Counts within 600 km Radius 2011-2018")
plt.show()
# plt.savefig('numobs.png', dpi=300)

