import pandas as pd
import gsw
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime
from scipy import interpolate
import csv
from helpers import get_g

print('Reading all hydrographic data...')
hydr_data = {}

def read_data(fname, hydr_data):
    data = pd.read_csv(fname)

    dt = data['Datetime'].values
    salinity = data['Salinity'].values
    latitude = data['Latitude'].values  
    longitude = data['Longitude'].values  
    depth = data['Depth'].values  

    print('Set the data with key as lat lon and val as T/S/P/D/SSH...')
    for idx in range(len(latitude)):
        
        latitude[idx], longitude[idx] = round(latitude[idx],5), round(longitude[idx],5)
        ts = datetime.strptime(dt[idx], "%Y-%m-%d %H:%M:%S")
        
        # take only summer months measurements to remove bias
        # if ts.month == 6 or ts.month == 7 or ts.month == 8:
            
        if (latitude[idx],longitude[idx]) not in list(hydr_data.keys()):
            hydr_data[(latitude[idx], longitude[idx])] = {'dt': ts.date(), 'sali':[], 'dept':[]}
            
        hydr_data[(latitude[idx], longitude[idx])]['sali'].append(salinity[idx])
        hydr_data[(latitude[idx], longitude[idx])]['dept'].append(depth[idx])

    # print(hydr_data)
    return hydr_data

hydr_data = read_data('data/2011.csv', hydr_data)
hydr_data = read_data('data/2012.csv', hydr_data)
hydr_data = read_data('data/2013.csv', hydr_data)
hydr_data = read_data('data/2014.csv', hydr_data)
hydr_data = read_data('data/2015.csv', hydr_data)
hydr_data = read_data('data/2016.csv', hydr_data)
hydr_data = read_data('data/2017.csv', hydr_data)
hydr_data = read_data('data/2018.csv', hydr_data)
print('Done reading all hydrographic data...')

df = pd.read_csv('data_500m.csv')
df['D_Siso'] = np.full(len(df), np.nan)
df['hFW'] = np.full(len(df), np.nan)
print(df.head)

Sref=35
Siso=34 # isohaline

k=0
############## using specific volume anomaly method 
# for each latlon compute the dynamic height using t, s, p and absolute ssh 
for latlon, data in hydr_data.items():
    
    D = np.array(data['dept'])
    S = np.array(data['sali'])
    # print(D, S)
    
    try:
        if len(D)>0 and len(S)>0:
            idx = np.abs(S - Siso).argmin()
            # print(idx, D[idx], S[idx])
                
            # depth at 34 isohaline
            hydr_data[latlon]['D_Siso'] = D[idx]
            df.loc[(df['Latitude'] == latlon[0]) & (df['Longitude'] == latlon[1]), 'D_Siso'] = hydr_data[latlon]['D_Siso']
            
            hfw = 0
            for i in range(idx+1):
                dz = D[i+1]-D[i]
                hfw = hfw + (Sref-S[i])*dz/Sref
                # print(i, D[i], D[i+1], S[i], hfw)

            hydr_data[latlon]['hFW'] = round(hfw,5)
            df.loc[(df['Latitude'] == latlon[0]) & (df['Longitude'] == latlon[1]), 'hFW'] = hydr_data[latlon]['hFW']
            # print(hfw)
    except IndexError as err:
        k=k+1
        # continue

print(k)
print(df.head)
# df.to_csv('2012.csv', index=False)
df.to_csv('data_500m_fw.csv', index=False)    # for tac 2012 month
   
