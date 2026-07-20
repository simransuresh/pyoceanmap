import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from geopy.distance import geodesic
from datetime import date, timedelta


# ----------------------------------
# Seasonal window
# ----------------------------------
def get_seas(month):
    """
    Return the 5-month seasonal window centered on ``month`` (wrapping
    around the year boundary), used to restrict which observations are
    considered seasonally comparable to a given target month.

    Parameters
    ----------
    month : int
        Month number (1-12).

    Returns
    -------
    tuple of int
        The 5 months in the window, e.g. ``get_seas(1) == (11, 12, 1, 2, 3)``.
    """
    if month == 1:
        return (11, 12, 1, 2, 3)
    if month == 2:
        return (12, 1, 2, 3, 4)
    if month == 11:
        return (9, 10, 11, 12, 1)
    if month == 12:
        return (10, 11, 12, 1, 2)

    return (month - 2, month - 1, month, month + 1, month + 2)


# ----------------------------------
# Gravity
# ----------------------------------
def get_g(lat):
    """
    Latitude-dependent gravitational acceleration (International Gravity
    Formula), used to convert dynamic height (geopotential) to a
    sea-surface-height-like quantity in meters.

    Parameters
    ----------
    lat : float or array-like
        Latitude in degrees.

    Returns
    -------
    float or ndarray
        Gravitational acceleration in m/s^2.
    """
    g0 = 9.780327
    phi = np.radians(lat)
    return g0 * (1 + 0.0053024 * np.sin(phi)**2 - 0.0000058 * np.sin(2 * phi)**2)


# ----------------------------------
# Coriolis
# ----------------------------------
def coriolis(lat):
    """
    Coriolis parameter f = 2 * Omega * sin(latitude).

    Parameters
    ----------
    lat : float or array-like
        Latitude in degrees.

    Returns
    -------
    float or ndarray
        Coriolis parameter in rad/s.
    """
    omega = 7.2921e-5
    return 2 * omega * np.sin(np.radians(lat))


# ----------------------------------
# Signal / Noise
# ----------------------------------
def signal(Od, n):
    """
    Signal variance of a set of observations, used as the a priori
    variance (s2) in the objective mapping covariance functions.

    Parameters
    ----------
    Od : array-like
        Observed values.
    n : int
        Number of observations (``len(Od)``).

    Returns
    -------
    float
        Signal variance.
    """
    return np.sum((Od - np.mean(Od))**2) / n


def noise(obs_coords, Od, n):
    """
    Noise variance estimated from the mean squared difference between each
    observation and its nearest spatial neighbor, used as the diagonal
    (measurement-error) term added to the covariance matrix in objective
    mapping.

    Parameters
    ----------
    obs_coords : array-like of (lat, lon) tuples
        Observation locations.
    Od : array-like
        Observed values, in the same order as ``obs_coords``.
    n : int
        Number of observations.

    Returns
    -------
    float
        Noise variance. Returns 0.0 if there are fewer than 2 observations.
    """
    if len(Od) <= 1:
        return 0.0

    tree = cKDTree(np.array(obs_coords))
    n2 = 0.0

    for i, point in enumerate(obs_coords):
        _, idx = tree.query(point, k=2)
        nearest_idx = idx[1]
        n2 += (Od[i] - Od[nearest_idx])**2

    return n2 / (2 * n)


# ----------------------------------
# Distance matrix
# ----------------------------------
def D_mat(subset, target=None):
    """
    Geodesic distance(s) in kilometers between points.

    Parameters
    ----------
    subset : tuple of (lat, lon), or list of (lat, lon) tuples
        If a single (lat, lon) tuple, computed against ``target``. If a
        list of points and ``target`` is given, returns the distance from
        each point to ``target``. If a list of points and ``target`` is
        None, returns the full pairwise distance matrix.
    target : tuple of (lat, lon), optional
        Target point.

    Returns
    -------
    float or ndarray
        A scalar distance, a 1-D array of distances, or a 2-D pairwise
        distance matrix, depending on the inputs (see above).
    """
    if isinstance(subset, tuple):
        return geodesic(subset, target).km

    if target is not None:
        return np.array([
            geodesic(point, target).km for point in subset
        ])

    return np.array([
        [geodesic(subset[i], subset[j]).km for j in range(len(subset))]
        for i in range(len(subset))
    ])


# ----------------------------------
# Potential Vorticity matrix
# ----------------------------------
def PV_mat(latd, lond, latg, long, depth_info):
    """
    Normalized potential-vorticity (f/Z) difference metric between data
    points and grid points, used alongside geodesic distance in the
    objective mapping covariance functions so that interpolation respects
    bathymetric/dynamical similarity, not just proximity.

    Parameters
    ----------
    latd, lond : array-like
        Latitudes/longitudes of the data (observation) points.
    latg, long : float or array-like
        Latitude(s)/longitude(s) of the target grid point(s).
    depth_info : dict
        Mapping from ``(round(lat, 5), round(lon, 5))`` to
        ``{"depth": float}``, as built by
        :func:`pyoceanmap.mapping.build_depth_info`.

    Returns
    -------
    ndarray
        PV difference matrix of shape ``(len(latd), len(latg))``. Entries
        are NaN where the depth lookup is missing or zero.
    """

    latd = np.array(latd)
    lond = np.array(lond)

    latg = np.atleast_1d(latg)
    long = np.atleast_1d(long)

    fd = coriolis(latd)
    fg = coriolis(latg)

    # safe depth lookup
    def safe_depth(lat, lon):
        key = (round(lat, 5), round(lon, 5))
        return depth_info.get(key, {}).get("depth", np.nan)

    Zd = np.array([safe_depth(lat, lon) for lat, lon in zip(latd, lond)])
    Zg = np.array([safe_depth(lat, lon) for lat, lon in zip(latg, long)])

    # avoid division by zero
    Zd = np.where(Zd == 0, np.nan, Zd)
    Zg = np.where(Zg == 0, np.nan, Zg)

    PV = np.abs(fd[:, None] / Zd[:, None] - fg / Zg) / np.sqrt(
        (fd[:, None] / Zd[:, None])**2 + (fg / Zg)**2
    )

    return PV


# ----------------------------------
# Covariance functions
# ----------------------------------
def covar1(D, PV, s2, L, phi):
    """
    Stage-1 objective mapping covariance: a Gaussian in distance ``D`` and
    potential-vorticity difference ``PV``.

    Parameters
    ----------
    D : float or ndarray
        Geodesic distance(s) in km.
    PV : float or ndarray
        Potential-vorticity difference(s).
    s2 : float
        Signal variance (see :func:`signal`).
    L : float
        Spatial decorrelation length scale (km).
    phi : float
        Potential-vorticity decorrelation scale.

    Returns
    -------
    float or ndarray
        Covariance value(s).
    """
    return s2 * np.exp(-(D / L)**2 - (PV / phi)**2)


def covar2(D, PV, t, s2, L, phi, tau):
    """
    Stage-2 objective mapping covariance: as :func:`covar1`, with an
    additional Gaussian decay in time difference ``t``.

    Parameters
    ----------
    D : float or ndarray
        Geodesic distance(s) in km.
    PV : float or ndarray
        Potential-vorticity difference(s).
    t : float or ndarray
        Time difference(s) in days.
    s2 : float
        Signal variance.
    L : float
        Spatial decorrelation length scale (km).
    phi : float
        Potential-vorticity decorrelation scale.
    tau : float
        Temporal decorrelation scale (days).

    Returns
    -------
    float or ndarray
        Covariance value(s).
    """
    return s2 * np.exp(-(D / L)**2 - (PV / phi)**2 - (t / tau)**2)


# ----------------------------------
# Time difference
# ----------------------------------
def tdiff(dates1, dates2=None):
    """
    Absolute difference in days between dates.

    Parameters
    ----------
    dates1 : datetime-like, or array-like of datetime-like
        A single date, or a collection of dates.
    dates2 : datetime-like, optional
        A single reference date to diff ``dates1`` against. If omitted,
        the full pairwise day-difference matrix within ``dates1`` is
        returned instead.

    Returns
    -------
    int, ndarray
        - If both ``dates1`` and ``dates2`` are single dates: a scalar
          day difference.
        - If ``dates1`` is a collection and ``dates2`` is given: a 1-D
          array of day differences.
        - If ``dates2`` is omitted: a 2-D pairwise day-difference matrix.
    """
    dates1 = pd.to_datetime(dates1)

    if dates2 is not None:
        dates2 = pd.to_datetime(dates2)

        if isinstance(dates1, pd.Timestamp) and isinstance(dates2, pd.Timestamp):
            return abs((dates1 - dates2).days)

        # dates1 may end up as a DatetimeIndex (no .dt accessor) or a Series
        # (.dt accessor only) depending on whether the caller passed a list
        # or a pandas Series, so go through .to_numpy() to avoid the accessor
        # mismatch and compute the day difference directly.
        diff = (dates1 - dates2).to_numpy().astype("timedelta64[D]").astype(int)
        return np.abs(diff)

    # matrix case
    dates1_np = dates1.to_numpy()
    diff = (dates1_np[:, None] - dates1_np[None, :]).astype("timedelta64[D]").astype(int)

    return np.abs(diff)
