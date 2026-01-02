import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

# -------------------------------
# Setup projection
# -------------------------------
m = Basemap(projection='nplaea', boundinglat=70, lon_0=0,
            resolution='l', round=True)

fig, axes = plt.subplots(1, 2, figsize=(12,6),
                         gridspec_kw={'wspace':0.05})

# ==========================================================
# SUBPLOT 1 — Observations
# ==========================================================
df1 = pd.read_csv("data_preparation/data_points.csv")

ax1 = axes[0]
m.ax = ax1
m.drawcoastlines(linewidth=1.2)
m.drawparallels([80], labels=[1,0,0,0], fontsize=7)
m.drawmeridians([-180,-90,0,90], labels=[0,0,0,1], fontsize=7)

x1, y1 = m(df1["Longitude"].values, df1["Latitude"].values)

sc1 = m.scatter(x1, y1, c=df1["Surf_DH"].values,
                s=20, cmap="YlGnBu",
                vmin=0, vmax=0.8)

ax1.set_title("Observed Surface DH (2009–2015)")

# ==========================================================
# SUBPLOT 2 — Gridded DH
# ==========================================================
df2 = pd.read_csv("results/grd_dh_2011_01.csv")
df2 = df2.dropna(subset=["Dynamic_Height", "DH_error"])

ax2 = axes[1]
m.ax = ax2
m.drawcoastlines(linewidth=1.2)
m.drawparallels([80], labels=[0,0,0,0], fontsize=7)
m.drawmeridians([-180,-90,0,90], labels=[0,0,0,1], fontsize=7)

x2, y2 = m(df2["Longitude"].values, df2["Latitude"].values)

sc2 = m.scatter(x2, y2, c=df2["Dynamic_Height"].values,
                s=20, cmap="YlGnBu",
                vmin=0, vmax=0.8)

ax2.set_title("Gridded Surface DH – Jan 2011")

# ==========================================================
# COMMON COLORBAR
# ==========================================================
cbar = fig.colorbar(sc2, ax=axes.ravel().tolist(),
                    orientation="vertical", shrink=0.8)
cbar.set_label("Dynamic Height (m)")

plt.savefig("figures/Observed_vs_Gridded_DH_201101.png", dpi=300, bbox_inches="tight")
plt.close()

