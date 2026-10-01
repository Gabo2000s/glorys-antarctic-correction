"""Extract the GLORYS12V1 station profiles used by the correction.

    python scripts/extract_glorys.py GLORYS.nc                 # writes outputs/glorys_extraction/
    python scripts/extract_glorys.py GLORYS.nc --compare       # and checks against data/raw/glorys
    python scripts/extract_glorys.py GLORYS.nc --positions table1 --out outputs/glorys_table1

Reproduces ``data/raw/glorys/GLORYS_Raw_Station_0XX.csv`` from a regional
GLORYS12V1 NetCDF file with daily mean ``thetao`` and ``so`` (the file used for
the published data covers 70-60 deg S, 70-60 deg W, 0.5-644 m, 1993-01-01 to
2025-12-23; it is not distributed with this repository).

Method, for each station and each depth level:

1. Select the daily field nearest to the station date.
2. Take the 2 grid points nearest to the station in latitude and the 2 nearest
   in longitude (a 2 x 2 block of 1/12 deg cells, about 9 km x 3.5 km here).
3. Compute the mean, median and standard deviation (ddof = 0) over the 4 cells,
   for potential temperature ``thetao`` (temp_*) and practical salinity ``so``
   (salt_*).

Station positions and dates (``--positions``), read from ``data/stations.csv``:

* ``confirmed`` (default): the confirmed station positions and UTC dates
  (``lat``, ``lon``, ``date``), used for the published files;
* ``table1``: the values printed in Table 1 of the August 2026 manuscript
  (``table1_*``), which differ for S1 and S4; kept only for comparison.

Requires numpy, pandas, xarray and netCDF4 (``pip install -e "python[extract]"``).
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STATIONS = ROOT / "data" / "stations.csv"
PUBLISHED = ROOT / "data" / "raw" / "glorys"
COLUMNS = ["depth", "temp_mean", "temp_median", "temp_std",
           "salt_mean", "salt_median", "salt_std"]
# The published S1 file is stored with 10 significant digits; the others
# with full precision. 1e-8 accepts that and nothing larger.
COMPARE_ATOL = 1e-8


def station_targets(positions: str) -> pd.DataFrame:
    """Station identifiers, positions (decimal degrees) and dates (YYYY-MM-DD)."""
    s = pd.read_csv(STATIONS)
    if positions == "confirmed":
        lat, lon, day = s.lat, s.lon, s.date
    elif positions == "table1":
        lat, lon, day = s.table1_lat, s.table1_lon, s.table1_date
    else:
        raise ValueError(positions)
    return pd.DataFrame({"station": s.station, "file_id": s.cast.str[-3:],
                         "lat": lat, "lon": lon, "day": day})


def extract_station(ds, lat: float, lon: float, day: str):
    """Statistics over the 2 x 2 grid cells nearest to (lat, lon) on `day`.

    Returns the profile table and a dict describing the cells used.
    """
    t = ds.sel(time=day, method="nearest")
    lat_idx = np.abs(t.latitude - lat).argsort()[:2].values
    lon_idx = np.abs(t.longitude - lon).argsort()[:2].values
    sub = t.isel(latitude=lat_idx, longitude=lon_idx)[["thetao", "so"]].load()
    dims = ["latitude", "longitude"]
    with warnings.catch_warnings():
        # Levels below the model seabed are NaN in all 4 cells; their std is NaN.
        warnings.simplefilter("ignore", RuntimeWarning)
        table = _statistics(sub, dims)
    cells = {"day_used": str(sub.time.values)[:10],
             "cell_lats": " ".join(f"{v:.4f}" for v in sub.latitude.values),
             "cell_lons": " ".join(f"{v:.4f}" for v in sub.longitude.values)}
    return table, cells


def _statistics(sub, dims) -> pd.DataFrame:
    return pd.DataFrame({
        "depth": sub.depth.values,
        "temp_mean": sub.thetao.mean(dim=dims).values,
        "temp_median": sub.thetao.median(dim=dims).values,
        "temp_std": sub.thetao.std(dim=dims).values,
        "salt_mean": sub.so.mean(dim=dims).values,
        "salt_median": sub.so.median(dim=dims).values,
        "salt_std": sub.so.std(dim=dims).values,
    })[COLUMNS]


def max_difference(a: pd.DataFrame, b: pd.DataFrame) -> float:
    """Largest |a - b|; inf if shapes or missing-value positions differ."""
    if a.shape != b.shape or not (a.isna() == b.isna()).all().all():
        return np.inf
    return float(np.nanmax((a - b).abs().to_numpy()))


def check_variables(ds) -> None:
    """Stop if the file does not hold the expected variables."""
    for var, std_name in (("thetao", "sea_water_potential_temperature"),
                          ("so", "sea_water_salinity")):
        if var not in ds:
            sys.exit(f"Variable '{var}' not found in the NetCDF file")
        got = ds[var].attrs.get("standard_name")
        if got and got != std_name:
            sys.exit(f"'{var}' has standard_name '{got}', expected '{std_name}'")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("netcdf", type=Path, help="regional GLORYS12V1 file with thetao and so")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "glorys_extraction")
    ap.add_argument("--positions", choices=("confirmed", "table1"), default="confirmed")
    ap.add_argument("--compare", action="store_true",
                    help="compare with the published files in data/raw/glorys")
    args = ap.parse_args(argv)

    import xarray as xr

    ds = xr.open_dataset(args.netcdf)
    check_variables(ds)
    args.out.mkdir(parents=True, exist_ok=True)

    log, failed = [], False
    for _, st in station_targets(args.positions).iterrows():
        table, cells = extract_station(ds, st.lat, st.lon, st.day)
        name = f"GLORYS_Raw_Station_{st.file_id}.csv"
        table.to_csv(args.out / name, index=False, lineterminator="\n")
        row = {"station": st.station, "file": name, "lat": st.lat, "lon": st.lon,
               "date": st.day, **cells}
        if args.compare:
            # Compare what was written to disk (as the correction reads it).
            written = pd.read_csv(args.out / name)[COLUMNS]
            diff = max_difference(written, pd.read_csv(PUBLISHED / name)[COLUMNS])
            row["max_abs_diff_vs_published"] = diff
            failed |= not diff <= COMPARE_ATOL
        log.append(row)
        print(f"{st.station} {name}: day {cells['day_used']}, cells lat [{cells['cell_lats']}] "
              f"lon [{cells['cell_lons']}]"
              + (f", max |diff| vs published {row['max_abs_diff_vs_published']:.1e}"
                 if args.compare else ""))

    pd.DataFrame(log).to_csv(args.out / "extraction_log.csv", index=False, lineterminator="\n")
    print(f"Outputs written to {args.out}")
    if args.compare:
        print("PASS: identical to the published files" if not failed
              else f"FAIL: differences above {COMPARE_ATOL:g}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
