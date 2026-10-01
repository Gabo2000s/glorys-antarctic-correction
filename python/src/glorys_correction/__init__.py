"""Adaptive thermodynamic correction of GLORYS12V1 profiles against CTD casts
in Marguerite Bay, Antarctic Peninsula."""

from .correction import (METRIC_NAMES, StationResult, correct_all,
                         correct_station, metrics_table)
from .stations import STATIONS, Station

__version__ = "1.0.0"

__all__ = [
    "METRIC_NAMES", "STATIONS", "Station", "StationResult",
    "correct_all", "correct_station", "metrics_table", "__version__",
]
