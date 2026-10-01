"""Tests of scripts/extract_glorys.py on a small synthetic GLORYS-like dataset."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

xr = pytest.importorskip("xarray")

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("extract_glorys", ROOT / "scripts" / "extract_glorys.py")
eg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eg)


def synthetic():
    """thetao = 1000 t + 100 d + 10 i + j  (t, d, i, j: time, depth, lat, lon indices);
    so = thetao + 0.5; the deepest level is missing everywhere (below the seabed)."""
    time = pd.date_range("2025-12-10", periods=6, freq="D")
    depth = np.array([0.5, 10.0, 100.0])
    lat = -68.5 + np.arange(6) / 12
    lon = -70.0 + np.arange(7) / 12
    t, d, i, j = np.meshgrid(np.arange(6), np.arange(3), np.arange(6), np.arange(7), indexing="ij")
    theta = (1000 * t + 100 * d + 10 * i + j).astype(float)
    theta[:, 2] = np.nan
    coords = {"time": time, "depth": depth, "latitude": lat, "longitude": lon}
    dims = ("time", "depth", "latitude", "longitude")
    return xr.Dataset(
        {"thetao": (dims, theta, {"standard_name": "sea_water_potential_temperature"}),
         "so": (dims, theta + 0.5, {"standard_name": "sea_water_salinity"})},
        coords=coords)


def test_uses_nearest_day_and_2x2_nearest_cells():
    ds = synthetic()
    # lat index 2 is nearest, then 3; lon index 4 is nearest, then 3
    lat = -68.5 + 2.3 / 12
    lon = -70.0 + 3.8 / 12
    table, cells = eg.extract_station(ds, lat, lon, "2025-12-12")
    assert cells["day_used"] == "2025-12-12"
    # 4 cells: 10 i + j for i in {2, 3}, j in {3, 4} -> 23, 24, 33, 34
    base = 1000 * 2 + np.array([0, 100])
    np.testing.assert_allclose(table.temp_mean[:2], base + 28.5)
    np.testing.assert_allclose(table.temp_median[:2], base + 28.5)
    np.testing.assert_allclose(table.temp_std[:2], np.sqrt(25.25))      # ddof = 0
    np.testing.assert_allclose(table.salt_mean[:2], base + 29.0)
    assert table.iloc[2, 1:].isna().all()                               # below the seabed
    assert list(table.columns) == eg.COLUMNS


def test_rejects_wrong_variables():
    ds = synthetic()
    ds["thetao"].attrs["standard_name"] = "sea_water_temperature"
    with pytest.raises(SystemExit):
        eg.check_variables(ds)


def test_max_difference_requires_same_missing_values():
    a = pd.DataFrame({"x": [1.0, np.nan]})
    assert eg.max_difference(a, pd.DataFrame({"x": [1.0, np.nan]})) == 0.0
    assert eg.max_difference(a, pd.DataFrame({"x": [1.0, 2.0]})) == np.inf
