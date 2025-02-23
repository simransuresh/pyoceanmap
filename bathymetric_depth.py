import netCDF4 as nc
import numpy as np
from pyproj import Proj, transform, Transformer
import xarray as xr
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from mpl_toolkits.basemap import Basemap
import cartopy.feature as cfeature
import pandas as pd

####### bathymetric depth given in meters from IBCAO dataset
# Open the original NetCDF file
print('Loading IBCAO bathymetric depth....')

ds = nc.Dataset('./data/IBCAO_v4_2_13_400m_ice.nc', 'r')

x = ds.variables['x'][:]
y = ds.variables['y'][:]
z = ds.variables['z'][:]    # in meters
z = np.where(z < 0, -z, np.nan) # only ocean
print(x.shape, y.shape, z.shape)

ds.close()
print('Loaded!', np.diff(x, axis=0).mean(), np.diff(y, axis=0).mean())


###### Plot the bathymetry
# fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': ccrs.NorthPolarStereo()})

# ax.set_extent([-180, 180, 70, 90], crs=ccrs.PlateCarree())
# ax.add_feature(cfeature.LAND, facecolor='white')
# ax.add_feature(cfeature.COASTLINE, edgecolor='black')
# ax.gridlines(color='gray', alpha=0.5, linestyle='--')

# xx, yy = np.meshgrid(x, y)
# im = ax.pcolormesh(xx, yy, z, cmap='YlGnBu', shading='auto')

# cbar = plt.colorbar(im, ax=ax, shrink=0.7)
# cbar.set_label("Bathymetric Depth (m)")

# # plt.savefig('bathy.png', dpi=300)
# plt.show()


###### calculate depth using nearest latlons (KD tree)
proj_polar = Proj(proj='stere', lat_ts=70, lon_0=0, lat_0=90, ellps='WGS84')
proj_wgs84 = Proj(proj='latlong', ellps='WGS84')

transformer = Transformer.from_proj(proj_polar, proj_wgs84)
xx, yy = np.meshgrid(x, y)
lon, lat = transformer.transform(xx, yy)

# form a KD tree which gives nearest depth z to a lat, lon
points = np.column_stack((lat.flatten(), lon.flatten()))
tree = cKDTree(points)

print('Ready to compute depths now...')

# finding closest depth in km to a grid point (negate depth as it is already negative or else sqrt(neg) will give err)
def nearest_depth(target_lat, target_lon):
    _, idx = tree.query([target_lat, target_lon])
    return z.flatten()[idx]/1000

# test
# print(nearest_depth(85, 60))
