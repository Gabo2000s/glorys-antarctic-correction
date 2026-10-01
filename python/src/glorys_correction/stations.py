"""Station list: identifiers and file names.

=======  ===================  ===========================  ===============
Station  CTD file             GLORYS extract               Figure label
=======  ===================  ===========================  ===============
S1       NF003_008.cnv        GLORYS_Raw_Station_008.csv   Station-01
S2       NF003_009.cnv        GLORYS_Raw_Station_009.csv   Station-02
S3       NF003_010.cnv        GLORYS_Raw_Station_010.csv   Station-03
S4       NF003_012.cnv        GLORYS_Raw_Station_012.csv   Station-04
S5       NF003_013.cnv        GLORYS_Raw_Station_013.csv   Station-05
S6       NF003_014.cnv        GLORYS_Raw_Station_014.csv   Station-06
=======  ===================  ===========================  ===============
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Station:
    key: str      # station, "S1".."S6"
    file_id: str  # "08".."14"
    label: str    # figure label, "Station-01".."Station-06"

    @property
    def cast(self) -> str:
        return f"NF003_0{self.file_id}"

    def ctd_path(self, data_dir: Path) -> Path:
        return Path(data_dir) / "ctd" / f"{self.cast}.cnv"

    def glorys_path(self, data_dir: Path) -> Path:
        return Path(data_dir) / "glorys" / f"GLORYS_Raw_Station_0{self.file_id}.csv"


STATIONS: tuple[Station, ...] = tuple(
    Station(f"S{i + 1}", fid, f"Station-{i + 1:02d}")
    for i, fid in enumerate(["08", "09", "10", "12", "13", "14"])
)
