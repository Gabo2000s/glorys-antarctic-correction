"""Unit tests of the numerical operations, with hand-computed expectations."""

import numpy as np

from glorys_correction import numerics as nm

nan = np.nan


def test_centred_gradient_on_non_uniform_grid():
    x = np.array([0.0, 1.0, 3.0, 6.0])
    f = x ** 2
    # ends: one-sided; interior: (f[i+1] - f[i-1]) / (x[i+1] - x[i-1])
    np.testing.assert_allclose(nm.centred_gradient(f, x), [1.0, 3.0, 7.0, 9.0])


def test_bin_median_bins_and_empty_bins():
    z = np.array([0.0, 0.4, 0.9, 2.2, 3.0])
    v = np.array([1.0, 3.0, 5.0, 7.0, 9.0])
    centres, med = nm.bin_median(z, v, 1.0)
    np.testing.assert_allclose(centres, [0.5, 1.5, 2.5])
    # [0,1): 1,3,5 -> 3 ; [1,2): empty ; [2,3]: 7 and 9 (last bin closed) -> 8
    np.testing.assert_array_equal(med, [3.0, nan, 8.0])


def test_moving_median_ignores_and_fills_nan():
    x = np.array([nan, 1.0, 2.0, 3.0])
    np.testing.assert_allclose(nm.moving_median(x, 3), [1.0, 1.5, 2.0, 2.5])


def test_moving_mean_truncates_window_at_the_ends():
    x = np.array([1.0, 2.0, 4.0, 8.0])
    np.testing.assert_allclose(nm.moving_mean(x, 3), [1.5, 7 / 3, 14 / 3, 6.0])


def test_savgol_is_exact_for_a_quadratic_including_the_ends():
    t = np.arange(21, dtype=float)
    x = 3.0 + 2.0 * t + 0.5 * t ** 2
    np.testing.assert_allclose(nm.savgol_smooth(x, 9), x, atol=1e-9)


def test_savgol_uses_full_window_at_the_ends():
    # At i = 0 the fit uses samples 0..4 (window of 5 shifted to the start).
    x = np.array([0.0, 1.0, 0.0, 1.0, 0.0, 5.0, 5.0])
    t = np.arange(5, dtype=float)
    coef = np.linalg.lstsq(np.vander(t, 3), x[:5], rcond=None)[0]
    assert abs(nm.savgol_smooth(x, 5)[0] - np.polyval(coef, 0.0)) < 1e-12


def test_fill_outliers_replaces_spike_by_linear_interpolation():
    x = np.array([1.0, 1.1, 0.9, 1.0, 8.0, 1.05, 0.95, 1.0, 1.1])
    expected = x.copy()
    expected[4] = (1.0 + 1.05) / 2
    np.testing.assert_allclose(nm.fill_outliers(x, 5), expected)


def test_pearson_r_uses_complete_pairs_only():
    a = np.array([1.0, 2.0, nan, 4.0, 5.0])
    b = np.array([2.0, 4.1, 6.0, nan, 9.9])
    keep = ~np.isnan(a) & ~np.isnan(b)
    da, db = a[keep] - a[keep].mean(), b[keep] - b[keep].mean()
    r = np.sum(da * db) / np.sqrt(np.sum(da ** 2) * np.sum(db ** 2))
    assert abs(nm.pearson_r(a, b) - r) < 1e-12
    assert abs(nm.pearson_r(a, 2 * a + 1) - 1.0) < 1e-12
