"""The correction reproduces the published metrics.

Reference values: metrics table (Table 2) of the associated article (bias,
RMSE and Pearson correlation, GLORYS minus CTD, before and after correction;
Conservative Temperature in degC, Absolute Salinity in g kg-1), and the
full-precision values in ``results/metrics.csv``.

Table 2 values below are those of the revised article:

* levels without GLORYS data set to missing (step 21): S2 corr_T_after 0.83,
  corr_S_after 0.94; S3 bias_T_after 0.05, rmse_S_after 0.25, corr_T_after
  0.89, corr_S_after 0.84;
* temperature computed as Conservative Temperature, with the GLORYS potential
  temperature converted by CT_from_pt: bias_T_before S1 0.08, S2 1.06,
  S3 0.47, S4 0.69, S5 0.79, S6 1.18; rmse_T_before S2 1.21, S3 0.72,
  S6 1.45; bias_T_after S4 -0.05; rmse_T_after S2 0.55, S4 0.34;
  corr_T_before S5 0.43; corr_T_after S6 0.81.
"""

from pathlib import Path

import gsw
import numpy as np
import pandas as pd

from glorys_correction import METRIC_NAMES, correct_all, metrics_table

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "raw"
RESULTS = ROOT / "results" / "metrics.csv"

ARTICLE_TABLE = pd.DataFrame(
    [
        [0.08, 0.16, -0.80, 0.14, 0.53, 0.28, 1.18, 0.21, 0.82, 0.97, 0.92, 0.91],
        [1.06, 0.17, -0.45, 0.16, 1.21, 0.55, 0.85, 0.22, 0.77, 0.83, 0.88, 0.94],
        [0.47, 0.05, -0.76, 0.16, 0.72, 0.34, 1.11, 0.25, 0.78, 0.89, 0.84, 0.84],
        [0.69, -0.05, -0.67, 0.11, 0.98, 0.34, 1.00, 0.18, 0.73, 0.93, 0.97, 0.96],
        [0.79, -0.02, -0.39, 0.14, 1.30, 0.55, 0.77, 0.20, 0.43, 0.67, 0.91, 0.96],
        [1.18, 0.01, -0.46, 0.12, 1.45, 0.45, 0.75, 0.18, 0.63, 0.81, 0.94, 0.96],
    ],
    index=[f"S{i}" for i in range(1, 7)],
    columns=list(METRIC_NAMES),
)

# The article prints two decimals, so a correct value can differ from the
# printed one by 0.005 from rounding alone; four cells were rounded from three
# decimals (e.g. 1.1746 -> 1.175 -> 1.18), so the largest difference is 0.0054.
ARTICLE_ATOL = 0.006

# Means and sums depend on summation order (library version, CPU), so bitwise
# equality is not expected across machines; 1e-9 is far below any meaningful
# change.
RESULTS_ATOL = 1e-9

_cache = {}


def _metrics():
    if "m" not in _cache:
        _cache["m"] = metrics_table(correct_all(DATA))
    return _cache["m"]


def test_reproduces_article_table():
    diff = (_metrics() - ARTICLE_TABLE).abs()
    assert diff.to_numpy().max() <= ARTICLE_ATOL, (
        f"max difference {diff.to_numpy().max():.4f} at {diff.stack().idxmax()}"
    )


def test_matches_published_results():
    expected = pd.read_csv(RESULTS, index_col="station")[list(METRIC_NAMES)]
    np.testing.assert_allclose(_metrics().to_numpy(), expected.to_numpy(),
                               rtol=0, atol=RESULTS_ATOL)


def test_corrected_profiles_exist_only_where_glorys_has_data():
    for res in correct_all(DATA):
        key = res.station.key
        np.testing.assert_array_equal(np.isnan(res.CT_corrected), np.isnan(res.CT_raw), key)
        np.testing.assert_array_equal(np.isnan(res.SA_corrected), np.isnan(res.SA_raw), key)


def test_metrics_before_and_after_use_the_same_levels():
    for res in correct_all(DATA):
        before = ~np.isnan(res.CT_raw) & ~np.isnan(res.CT_ctd)
        after = ~np.isnan(res.CT_corrected) & ~np.isnan(res.CT_ctd)
        np.testing.assert_array_equal(before, after, res.station.key)


def test_glorys_temperature_is_read_as_potential_temperature():
    # GLORYS thetao is potential temperature: converting the raw Conservative
    # Temperature back to potential temperature must return the file values.
    for res in correct_all(DATA):
        theta = pd.read_csv(res.station.glorys_path(DATA))["temp_median"].to_numpy()
        np.testing.assert_allclose(gsw.pt_from_CT(res.SA_raw, res.CT_raw), theta,
                                   rtol=0, atol=1e-10, err_msg=res.station.key)
