import pandas as pd
import csv
import netCDF4 as nc
from datetime import datetime

# filename AO_phys_oce_2011

# read UDAH nc file 
for year in range(1980, 2000):
    ds = nc.Dataset(f'data/UDAH/AO_phys_oce_{year}.nc', 'r')

    dt = ds.variables['Date'][:,:]
    lon = ds.variables['Lon'][:]
    lat = ds.variables['Lat'][:]    
    pres = ds.variables['Pres'][:]    
    dept = ds.variables['Depth'][:]    # in meters
    temp = ds.variables['Temp'][:]    
    sal = ds.variables['Sal'][:]    
    n = len(lon)
    print(n)

    ds.close()

    fp = open(f'data/pp_UDAH/{year}.csv', 'w+', newline='')
    writer = csv.writer(fp, delimiter=',')
    writer.writerow(['Datetime','Latitude','Longitude','Pressure','Depth', 'Temperature','Salinity'])

    for idx in range(n):
        # Convert the byte array to a string
        extracted_dt = ''.join([char.decode('utf-8') for char in dt[:, idx]])

        # Handle missing time (99:99) by replacing it with 00:00 or a placeholder time
        if '99:99' in extracted_dt:
            # Replace the time with 00:00 if it's missing
            extracted_dt = extracted_dt.replace('99:99', '00:00')
            date_obj = datetime.strptime(extracted_dt, '%Y-%m-%dT%H:%M')
        else:
            # Parse the full datetime if it is present
            date_obj = datetime.strptime(extracted_dt, '%Y-%m-%dT%H:%M')
            
        writer.writerow([date_obj, lat[idx], lon[idx], pres[idx], dept[idx], temp[idx], sal[idx]])
        
    fp.close()