from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

df = pd.read_csv('results/grd_dh_2011_01.csv')
#df = df.dropna(subset=["Dynamic_Height", "DH_error"])
#df = df[(df["Dynamic_Height"] < 10) & (df["Dynamic_Height"] > -10)]
#X = df['X_meters'].values
#Y = df['Y_meters'].values
lons = df['Longitude'].values
lats = df['Latitude'].values
dhs = df['Dynamic_Height'].values
#ug = df['ug'].values
#vg = df['vg'].values

print(df.head)

#### Plot dh
m = Basemap(projection='nplaea', boundinglat=70, lon_0=0, resolution='l', round=True)

fig, ax = plt.subplots(figsize=(8, 8))
m.drawcoastlines(linewidth=1.2)
m.drawparallels([80], labels=[True], linewidth=0.5, color='gray', fontsize=6)
m.drawmeridians([-180, -90, 0, 90], labels=[True, True, True, True], linewidth=0.5, color='gray', fontsize=6)

x, y = m(lons, lats)
sc = m.scatter(x, y, s=20, c=dhs, cmap='YlGnBu', vmin=0, vmax=0.8)
# scale = np.nanmax(np.sqrt(ug**2 + vg**2)) / 0.02
# q = m.quiver(x, y, ug, vg, scale=scale, color='black', width=0.003)

cbar = plt.colorbar(sc, ax=ax, shrink=0.7)
cbar.set_label("Dynamic height (m)")
## plt.show()

plt.title("Dynamic Height – January 2011 (NPLAEA native grid)")
plt.savefig("Gridded_DH_201101.png", dpi=300)
plt.close()

