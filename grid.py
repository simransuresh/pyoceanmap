import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

# generate grid with Lambert Equal Area projection setup
m = Basemap(projection='nplaea', boundinglat=60, lon_0=0, resolution='l', llcrnrlat=70, urcrnrlat=90,
            llcrnrlon=-180, urcrnrlon=180, round=True)
# print(-m.xmax, m.xmax, -m.ymax, m.ymax)

# Create grid
X, Y = np.meshgrid( np.arange(-m.xmax, m.xmax, 50000) , np.arange(-m.ymax, m.ymax, 50000) )

# Convert grid points to latitudes and longitudes
lons, lats = m(X, Y, inverse=True)

print('Spacing of new grid:', np.diff(X, axis=1).mean(), np.diff(Y, axis=0).mean())

# Save to CSV
grid_data = pd.DataFrame({ 'X_meters': X.ravel(), 'Y_meters': Y.ravel(), 
    'Longitude': lons.ravel(), 'Latitude': lats.ravel() })

grid_data = grid_data[(grid_data['Latitude']>=70) & (np.isfinite(grid_data['Latitude']))]
csv_path = 'grid_50km_nplaea.csv'
# grid_data.to_csv(csv_path, index=False)
# print(grid_data.head)


###### plot the grid generated
grid_data = pd.read_csv(csv_path)
X = grid_data['X_meters'].values
Y = grid_data['Y_meters'].values
lons = grid_data['Longitude'].values
lats = grid_data['Latitude'].values

fig, ax = plt.subplots(figsize=(10, 10))
m.drawcoastlines(linewidth=1.2)

sc = m.scatter(X, Y, s=10, c='red')
plt.show()


###### add depth to the new grid 
# from bathymetric_depth import nearest_depth

# depths = []
# for idx,row in grid_data.iterrows():
#     d = nearest_depth(row['Latitude'], row['Longitude'])
#     print(row['Latitude'], row['Longitude'], d)
#     depths.append(d)
    
# grid_data['Depth'] = np.array(depths)
# grid_data = grid_data.dropna(subset=['Depth'])

# print('Computed depths for grid points 50km!!')

# grid_data.to_csv(csv_path, index=False)
# print(grid_data.head, 'Depths saved!!')


###### plot of new grid with depth
# Create a scatter plot of the latitudes and longitudes
# grid_data = pd.read_csv(csv_path)
# grid_data = grid_data[grid_data['Depth']>0.5]   # only deep basins
# grid_data[(grid_data['Latitude']<82) & (grid_data['Longitude']>-100) & ((grid_data['Longitude']<90))] = np.nan # remove Fram strait
# grid_data = grid_data.dropna()

# X = grid_data['X_meters'].values
# Y = grid_data['Y_meters'].values
# lons = grid_data['Longitude'].values
# lats = grid_data['Latitude'].values
# d = grid_data['Depth'].values

# print(grid_data.head)

# fig, ax = plt.subplots(figsize=(10, 10))
# m.drawcoastlines(linewidth=1.2)

# sc = m.scatter(X, Y, s=5, c=d*1000, cmap='YlGnBu')
# cbar = plt.colorbar(sc, ax=ax, shrink=0.7)
# cbar.set_label("Bathymetric Depth (m)")

# # plt.show()
# plt.savefig('cao_50km_bathy.png', dpi=300)

# grid_data.to_csv(csv_path, index=False)  # grid to map now saved in grid_50km_nplaea.csv
