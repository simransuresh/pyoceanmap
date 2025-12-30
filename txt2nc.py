import pandas as pd
import netCDF4 as nc
import numpy as np

txt_file = "data/ArcticOcean_phys_oce_2015.txt"
out_nc   = "data/AO_phys_oce_2015.nc"

# ----------------------------------------------------
# Read fixed-width text file
# ----------------------------------------------------
df = pd.read_csv(txt_file, delim_whitespace=True)

# Combine date + time already in one column in your file
df["Datetime"] = df["yyyy-mm-ddThh:mm"]

nobs = len(df)
strlen = 16   # '2009-01-25T22:03' = 16 characters

# ----------------------------------------------------
# Create NetCDF
# ----------------------------------------------------
ds = nc.Dataset(out_nc, "w", format="NETCDF4")

ds.createDimension("nobs", nobs)
ds.createDimension("strlen", strlen)

Date  = ds.createVariable("Date", "S1", ("strlen", "nobs"))
Lon   = ds.createVariable("Lon", "f4", ("nobs",))
Lat   = ds.createVariable("Lat", "f4", ("nobs",))
Pres  = ds.createVariable("Pres", "f4", ("nobs",))
Depth = ds.createVariable("Depth", "f4", ("nobs",))
Temp  = ds.createVariable("Temp", "f4", ("nobs",))
Sal   = ds.createVariable("Sal", "f4", ("nobs",))

# ----------------------------------------------------
# Write data
# ----------------------------------------------------
Lon[:]   = df["Longitude_[deg]"].values
Lat[:]   = df["Latitude_[deg]"].values
Pres[:]  = df["Pressure_[dbar]"].values
Depth[:] = df["Depth_[m]"].values
Temp[:]  = df["Temp_[°C]"].values
Sal[:]   = df["Salinity_[psu]"].values

# Write Date as char array
for i, t in enumerate(df["Datetime"]):
    t = str(t).ljust(strlen)  # pad with spaces
    Date[:, i] = nc.stringtochar(np.array(t, dtype=f"S{strlen}"))

ds.close()

print("NetCDF file written:", out_nc)

