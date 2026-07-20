import numpy as np
import pandas as pd

from pyoceanmap.utils import (
    get_g,
    coriolis,
    D_mat,
    PV_mat,
    covar1,
    covar2,
    tdiff,
    signal,
    noise,
    get_seas,
)


def test_get_g_is_within_physical_range():
    for lat in [-90, -45, 0, 45, 90]:
        g = get_g(lat)
        assert 9.7 < g < 9.9


def test_coriolis_zero_at_equator_and_signed_by_hemisphere():
    assert np.isclose(coriolis(0), 0.0, atol=1e-12)
    assert coriolis(45) > 0
    assert coriolis(-45) < 0


def test_d_mat_known_geodesic_distance():
    # Roughly 1 degree of latitude ~= 111 km
    d = D_mat((0.0, 0.0), (1.0, 0.0))
    assert 108 < d < 113


def test_d_mat_vector_and_matrix_forms():
    points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    to_target = D_mat(points, target=(0.0, 0.0))
    assert to_target.shape == (3,)
    assert np.isclose(to_target[0], 0.0, atol=1e-6)

    full = D_mat(points)
    assert full.shape == (3, 3)
    assert np.allclose(np.diag(full), 0.0, atol=1e-6)


def test_pv_mat_uses_rounded_depth_lookup():
    depth_info = {(1.0, 2.0): {"depth": 100.0}, (3.0, 4.0): {"depth": 200.0}}
    pv = PV_mat([1.0], [2.0], 3.0, 4.0, depth_info)
    assert pv.shape == (1, 1)
    assert np.isfinite(pv[0, 0])


def test_pv_mat_missing_or_zero_depth_yields_nan():
    depth_info = {(1.0, 2.0): {"depth": 0.0}}
    pv = PV_mat([1.0], [2.0], 5.0, 6.0, depth_info)
    assert np.isnan(pv[0, 0])


def test_covar_decays_with_distance():
    near = covar1(D=10, PV=0, s2=1.0, L=100, phi=1)
    far = covar1(D=1000, PV=0, s2=1.0, L=100, phi=1)
    assert near > far > 0

    near2 = covar2(D=10, PV=0, t=0, s2=1.0, L=100, phi=1, tau=60)
    far2 = covar2(D=10, PV=0, t=1000, s2=1.0, L=100, phi=1, tau=60)
    assert near2 > far2 > 0


def test_tdiff_scalar_vector_and_matrix():
    assert tdiff("2020-01-01", "2020-01-11") == 10

    series = pd.Series(pd.to_datetime(["2020-01-01", "2020-01-05"]))
    diffs = tdiff(series, "2020-01-11")
    assert list(diffs) == [10, 6]

    matrix = tdiff(series)
    assert matrix.shape == (2, 2)
    assert matrix[0, 1] == 4


def test_signal_and_noise_on_synthetic_arrays():
    Od = np.array([1.0, 2.0, 3.0, 4.0])
    n = len(Od)
    sig = signal(Od, n)
    assert sig > 0

    coords = [(0.0, 0.0), (0.01, 0.0), (10.0, 10.0), (10.01, 10.0)]
    noise_var = noise(coords, Od, n)
    assert noise_var >= 0


def test_get_seas_wraps_around_year_boundary():
    assert get_seas(1) == (11, 12, 1, 2, 3)
    assert get_seas(12) == (10, 11, 12, 1, 2)
    assert get_seas(6) == (4, 5, 6, 7, 8)
