"""Reader for Sea-Bird ``.cnv`` files.

Returns every channel under its short name from the header (``depSM``,
``tv290C``, ``sal00``, ``c0S/m`` -> ``c0S_m``, ``flag``), the NMEA position
in signed decimal degrees, and converts ``bad_flag`` values to NaN.

Sign convention: ``68 09.73 S`` / ``069 32.12 W`` become ``-68.16217`` /
``-69.53533``. The sign matters because ``gsw.SA_from_SP`` uses longitude and
latitude to look up the Absolute Salinity Anomaly.

The header position and time are the confirmed station position and time,
also listed in ``data/stations.csv``. The correction uses the header position.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_NAME_RE = re.compile(r"^#\s*name\s+(\d+)\s*=\s*([^:]+):")
_BADFLAG_RE = re.compile(r"^#\s*bad_flag\s*=\s*(\S+)")
_LAT_RE = re.compile(r"^\*\s*NMEA Latitude\s*=\s*(\d+)\s+([\d.]+)\s*([NS])", re.I)
_LON_RE = re.compile(r"^\*\s*NMEA Longitude\s*=\s*(\d+)\s+([\d.]+)\s*([EW])", re.I)


def _sanitize(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]", "_", name.strip())


def _signed_degrees(deg: str, minutes: str, hemi: str, negative: str) -> float:
    value = float(deg) + float(minutes) / 60.0
    return -value if hemi.upper() == negative else value


@dataclass
class CnvData:
    """Contents of a ``.cnv`` file. Channels are also available as attributes."""

    columns: dict = field(default_factory=dict)
    latitude: float = np.nan
    longitude: float = np.nan
    bad_flag: float = np.nan
    header: list = field(default_factory=list)

    def __getattr__(self, item):
        cols = self.__dict__.get("columns", {})
        if item in cols:
            return cols[item]
        raise AttributeError(item)


def read_cnv(path: str | Path) -> CnvData:
    """Read a Sea-Bird ``.cnv`` file."""
    names: dict[int, str] = {}
    lat = lon = bad_flag = np.nan
    header: list[str] = []
    rows: list[list[float]] = []
    in_data = False

    with open(path, "r", encoding="latin-1") as fh:
        for line in fh:
            s = line.rstrip("\r\n")
            if in_data:
                if s.strip():
                    rows.append([float(v) for v in s.split()])
                continue
            header.append(s)
            if s.strip() == "*END*":
                in_data = True
            elif m := _NAME_RE.match(s):
                names[int(m.group(1))] = _sanitize(m.group(2))
            elif m := _BADFLAG_RE.match(s):
                bad_flag = float(m.group(1))
            elif m := _LAT_RE.match(s):
                lat = _signed_degrees(*m.groups(), negative="S")
            elif m := _LON_RE.match(s):
                lon = _signed_degrees(*m.groups(), negative="W")

    arr = np.asarray(rows, dtype=float)
    if arr.size == 0:
        raise ValueError(f"{path}: no data found after *END*")
    if np.isfinite(bad_flag):
        arr[np.isclose(arr, bad_flag, rtol=0.0, atol=abs(bad_flag) * 1e-6)] = np.nan

    columns = {names.get(j, f"col{j}"): arr[:, j] for j in range(arr.shape[1])}
    return CnvData(columns=columns, latitude=lat, longitude=lon,
                   bad_flag=bad_flag, header=header)
