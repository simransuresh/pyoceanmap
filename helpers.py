import numpy as np
from scipy.spatial import cKDTree
from geopy.distance import geodesic
import pandas as pd
from datetime import date, timedelta

# gives seasonal months ie. to map for Dec, data points during Nov, Dec, Jan are taken
def get_seas(month):
    if month==1:
        return 11, 12, 1, 2, 3
    if month==2:
        return 12, 1, 2, 3, 4
    if month==11:
        return 9, 10, 11, 12, 1
    if month==12:
        return 10, 11, 12, 1, 2

    return month-2, month-1, month, month+1, month+2

def convert_time(time):
    reference_date = date(2011, 1, 1)
    # time = days since 1st January 0000 at 00:00:00
    offset_days = [day - time[0] for day in time]
    # from ref, compute days in y-m format
    time = [ (reference_date+timedelta(days=day) ).strftime('%Y-%m') for day in offset_days]
    return time


def get_g(lat):
    # Define constants
    g0 = 9.780327  # Standard gravity at the equator in m/s^2
    phi = np.radians(lat) 
    g = g0 * (1 + 0.0053024 * np.sin(phi)**2 - 0.0000058 * np.sin(2 * phi)**2)
    return g


def coriolis(lat):
    # Earth rotation rate in rad/s
    Omg = 7.2921e-5
    return 2 * Omg * np.sin(np.radians(lat))

def find_nearest_coords(lat, lon, df, min_distance=49, max_distance=51):
    distances = []
    
    # Loop through each row in the dataframe to compute the distance
    for idx, row in df.iterrows():
        other_lat = row['Latitude']
        other_lon = row['Longitude']
        
        # Skip comparing to the same point
        if lat == other_lat and lon == other_lon:
            continue
        
        # Compute distance using haversine
        dist = D_mat((lat, lon), (other_lat, other_lon))
        
        if min_distance <= dist <= max_distance:
            distances.append((idx, other_lat, other_lon, dist))  # Including index
    
    # Sort by distance and return the 4 nearest points (with index)
    distances_sorted = sorted(distances, key=lambda x: x[3])  # Sort by distance (4th item)
    
    return distances_sorted[:4] # Return the top 4 nearest points

# signal variance
def signal(Od, n):
    return np.sum([(dval - np.mean(Od))**2 for dval in Od])/n

# noise variance 
def noise(obs_coords, Od, n):
    # Finding noise between a data point with its nearest neighbour using k-d tree
    tree = cKDTree(np.array(obs_coords))
    n2 = 0
    
    if len(Od)==1:
        return n2
    
    for i, point in enumerate(obs_coords):
        dist, idx = tree.query(point, k=2)  # k=2 because the closest point to a point is itself
        nearest_idx = idx[1]  # idx[0] is the point itself, idx[1] is the nearest neighbor
        n2 = n2 + (Od[i] - Od[nearest_idx])**2
        
    return n2/(2*n)

def D_mat(subset, target=None):
    if type(subset)==tuple: # 2 point distance for selection
        return geodesic(subset, target).km
    
    if target is not None:  # between grid and data points
        return np.array([ 
            geodesic(point, target).km for point in subset
        ])

    return np.array([ [     # between data points
        geodesic(subset[i], subset[j]).km for j in range(len(subset)) ] 
        for i in range(len(subset))
    ])
    
def PV_mat(latd, lond, latg, long, depth_info):
    # Compute Coriolis force for data points and grid points
    fd = 2 * 7.29e-5 * np.sin(np.deg2rad(latd))  # Coriolis force at data points
    fg = 2 * 7.29e-5 * np.sin(np.deg2rad(latg))  # Coriolis force at grid points

    # Ensure latitude and longitude pairs are in the correct shape for depth lookup
    data_coords = np.column_stack((latd, lond))  # Shape (N, 2)
    grid_coords = np.column_stack((latg, long))  # Shape (M, 2)

    # Retrieve bathymetric depth for data points and grid point using depth_info
    Zd = np.array([depth_info[(lat, lon)]['depth'] for lat, lon in data_coords])  # Depth at data points, shape (N,)
    Zg = np.array([depth_info[(lat, lon)]['depth'] for lat, lon in grid_coords])  # Depth at grid point(s), shape (M,)

    # Calculate PV matrix between all data points (n x n)
    return np.abs(fd[:, None] / Zd[:, None] - fg / Zg) / np.sqrt((fd[:, None] / Zd[:, None])**2 + (fg / Zg)**2)
 
# Function to compute covariance based on distance and PV
def covar1(D, PV, s2, L, phi):
    return s2 * np.exp(-(D / L)**2 - (PV / phi)**2)

def covar2(D, PV, t, s2, L, phi, tau):
    return s2 * np.exp(-(D / L)**2 - (PV / phi)**2 - (t / tau)**2)

def tdiff(dates1, dates2=None):
    # Convert dates1 to pandas datetime objects
    dates1 = pd.to_datetime(dates1)
    
    # Case 1: Difference between two individual dates
    if dates2 is not None:
        dates2 = pd.to_datetime(dates2)
        # If both are single dates, return the difference
        if isinstance(dates1, pd.Timestamp) and isinstance(dates2, pd.Timestamp):
            return np.abs((dates1 - dates2).days)
        
        # Case 2: Difference between a date array and a single date
        if isinstance(dates1, pd.Series) or isinstance(dates1, pd.DatetimeIndex):
            dates1_np = dates1.to_numpy()
            dates2_np = pd.to_datetime(dates2).to_numpy()  # Convert target date to numpy
            return np.abs((dates1_np - dates2_np).astype('timedelta64[D]').astype(int))

    # Case 3: Difference between dates in an array (matrix form)
    dates1_np = dates1.to_numpy()  # Convert dates array to numpy array
    date_diff_matrix = (dates1_np[:, None] - dates1_np[None, :]).astype('timedelta64[D]').astype(int)
    
    return np.abs(date_diff_matrix)
    
dp = pd.read_csv('data_points.csv')
dp_depth = {
    (row['Latitude'], row['Longitude']): {
        'depth': row['Depth'],
    }
    for _, row in dp.iterrows()
}

gp = pd.read_csv('grid_50km_nplaea.csv')
gp_depth = {
    (row['Latitude'], row['Longitude']): {
        'depth': row['Depth'],
    }
    for _, row in gp.iterrows()
}

depth_info = dp_depth | gp_depth

