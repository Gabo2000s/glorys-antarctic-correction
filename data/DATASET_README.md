# CTD casts and corrected GLORYS12V1 profiles, Marguerite Bay, December 2025

<!-- TODO before publishing: resolve every item marked TODO in this file. -->

Six CTD casts collected in Marguerite Bay (western Antarctic Peninsula) on
11–15 December 2025 during cruise NF003 of RV *Noosfera* (30th Ukrainian
Antarctic Expedition), the GLORYS12V1 reanalysis profiles extracted at each
station, and the GLORYS profiles after the adaptive thermodynamic correction
described in the associated article.

- **Article:** Morales-Acuña, E., Linero-Cueto, J., Manrique-Cantillo, A.,
  Gutiérrez-Cardenas, G., Escobedo-Urías, D., Olarte-García, C., and
  Dikul, N.: An adaptive thermodynamic correction framework for GLORYS ocean
  reanalysis in a coastal Antarctic fjord, TODO journal, TODO DOI.
- **Software:** glorys-antarctic-correction v1.0.0, TODO software DOI
  (https://github.com/Gabo2000s/glorys-antarctic-correction).

## Contents

| Path | Files | Description |
|---|---|---|
| `ctd/` | `NF003_0XX.cnv` (6) | Sea-Bird CTD casts, as converted by Seasave (ASCII `.cnv`) |
| `glorys/` | `GLORYS_Raw_Station_0XX.csv` (6) | GLORYS12V1 temperature and salinity statistics at each station |
| `corrected/` | `NF003_0XX_corrected_profile.csv` (6) | CTD, raw GLORYS and corrected GLORYS profiles on the GLORYS levels |
| `stations.csv` | 1 | Station metadata (see "Station metadata") |
| `MD5SUMS.txt`, `SHA256SUMS.txt` | 2 | Checksums of every file |

Station numbering: S1–S6 in the article correspond to casts NF003_008, 009,
010, 012, 013 and 014, and to the figure labels Station-01 … Station-06.

## Variables

### `ctd/*.cnv`

Sea-Bird SBE 19plus V2 SeaCAT profiler sampling at 4 Hz, mounted on an SBE 32
carousel with 24 Niskin bottles (temperature and conductivity sensor
S/N 8356). The profiler was soaked at 10 m for 3 min and lowered at about
1 m s⁻¹ to within 20 m of the seabed. Raw frequencies were converted to
engineering units with Sea-Bird software (Seasave V 7.26.7.121, as recorded
in each header). The factory calibration was used; no bottle salinities were
analysed. On 17 December 2025 a comparison cast at the Rothera Time Series
(RaTS) site agreed with the station instrument over the full depth.

TODO (data collectors): calibration date. The headers record sensor
calibrations of 31 Jan 2024 (temperature, conductivity) and 23 Jan 2024
(pressure); the article states 01.12.2026.

ASCII header followed by five columns after `*END*`:

| Column | Name | Units |
|---|---|---|
| 1 | `depSM` depth, salt water | m |
| 2 | `tv290C` temperature, ITS-90 | °C |
| 3 | `sal00` Practical Salinity | PSS-78 |
| 4 | `c0S/m` conductivity | S m⁻¹ |
| 5 | `flag` | – |

The files contain depth (`depSM`, derived from pressure) rather than
pressure. TODO (data collectors): processing modules applied after
conversion (filters, alignment, loop edit), if any.

### `glorys/*.csv`

One row per GLORYS12V1 vertical level (33 levels, 0.494–643.6 m) at each
station; missing values below the model seabed.

| Column | Units | Description |
|---|---|---|
| `depth` | m | GLORYS level depth |
| `temp_mean`, `temp_median`, `temp_std` | °C | Potential temperature (`thetao`, `sea_water_potential_temperature`) |
| `salt_mean`, `salt_median`, `salt_std` | PSS-78 | Practical salinity (`so`) |

Extraction, reproducible with `scripts/extract_glorys.py` of the software
repository:

1. **Source file:** daily mean `thetao` and `so` of GLORYS12V1 (Copernicus
   Marine Service, https://doi.org/10.48670/moi-00021) over 70–60° S,
   70–60° W, 0.494–643.6 m, 1993-01-01 to 2025-12-23, downloaded with the
   `copernicusmarine` toolbox (v2.2.4).
2. **Day:** the daily field nearest to the station date.
3. **Cells:** the 2 grid points nearest to the station in latitude and the 2
   nearest in longitude, a 2 × 2 block of 1/12° cells (about 9 km × 3.5 km
   at 68° S).
4. **Statistics:** mean, median and standard deviation (population, ddof = 0)
   over the 4 cells at each level. The correction uses the medians.

Positions and dates are the confirmed station positions and dates (`lat`,
`lon`, `date` in `stations.csv`).

The extraction script regenerates the six files from the source NetCDF file:
five are identical to the values stored here, and S1 differs by at most
5 × 10⁻⁹, because its file was saved with 10 significant digits.

The source file was downloaded on 14 February 2026.

### `corrected/*.csv`

One row per GLORYS level. Profiles are on the GLORYS depth levels; CTD values
are the quality-controlled, 1 m-binned cast interpolated onto those levels
(NaN where the cast does not reach a level). Corrected values are NaN where
GLORYS has no data.

| Column | Units | Description |
|---|---|---|
| `depth_m` | m | GLORYS level depth |
| `pressure_dbar` | dbar | Sea pressure from depth (TEOS-10) |
| `SA_ctd_gkg` | g kg⁻¹ | CTD Absolute Salinity |
| `CT_ctd_degC` | °C | CTD Conservative Temperature |
| `SA_glorys_raw_gkg` | g kg⁻¹ | GLORYS Absolute Salinity before correction |
| `CT_glorys_raw_degC` | °C | GLORYS Conservative Temperature before correction |
| `SA_glorys_corrected_gkg` | g kg⁻¹ | GLORYS Absolute Salinity after correction |
| `CT_glorys_corrected_degC` | °C | GLORYS Conservative Temperature after correction |
| `N2_s-2` | s⁻² | Buoyancy frequency squared from the CTD (negative values set to 0) |
| `turner_angle_deg` | ° | Turner angle from the CTD |
| `w_surface` | – | Surface weight, exp(−z / 80 m) |
| `w_structure` | – | Stratification weight, N² / max(N²) |
| `diffusive_convection` | 0/1 | 1 where −90° < Tu < −45° |

Temperature note: the algorithm works in Conservative Temperature Θ
(TEOS-10). The CTD in-situ temperature is converted with `gsw.CT_from_t`; the
GLORYS `thetao` is potential temperature and is converted with
`gsw.CT_from_pt`. Here Θ and potential temperature differ by up to 0.009 °C
(CTD) and 0.026 °C (GLORYS).

## Station metadata (`stations.csv`)

| Column | Units | Description |
|---|---|---|
| `station`, `cast`, `figure_label` | – | S1–S6, CTD file name, label in the figures |
| `date`, `time_utc` | – | Confirmed date and UTC time of the cast |
| `lat`, `lon` | ° | Confirmed position (signed decimal degrees, south and west negative) |
| `max_cast_depth_m` | m | Deepest sample of the cast (`depSM` in the `.cnv` file) |
| `table1_*` | – | Date, position and depths printed in Table 1 of the August 2026 manuscript, for reference |

The confirmed positions and dates are those recorded in the `.cnv` headers;
the correction and the GLORYS extraction use them. Stations are numbered by
cast file (NF003_008 … 014), not chronologically: S2 (11 Dec), S3 (12 Dec),
S4 (14 Dec), S5, S6 and S1 (15 Dec).

The manuscript's Table 1 differs from the confirmed values:

1. **S1 (NF003_008):** confirmed 15 Dec 2025, 68°09.73′ S, 69°32.12′ W;
   Table 1 gives 11 Dec 2025 at a position 572 m away. The source file is
   `NF003_008_a.hex`, and the cast reaches 624.6 m, deeper than both depths
   in Table 1 (590 m and 603 m).
2. **S4 (NF003_012):** confirmed 14 Dec 2025; Table 1 gives 15 Dec.
3. **Depth columns:** 'Max. cast depth' exceeds 'Water depth' at every
   station, although the casts stopped about 20 m above the seabed; the
   'Water depth' column matches the deepest sample of S2–S6 (within 8 m). The
   two columns appear to be swapped. TODO: water depth at each station,
   including the confirmed S1 position.

## Known limitations of the corrected profiles

- **Levels without GLORYS data** (below the model seabed) are missing (`NaN`)
  in the corrected profiles: S2 at 541–644 m, S3 at 318–644 m, S4 and S6 at
  644 m. The metrics before and after correction therefore use the same
  levels.
- **Levels without CTD data** keep a corrected value but are not validated
  against observations: the 0.5 m level at every station, S1 at 644 m, S5 at
  541–644 m and S6 at 541 m. In these levels the correction relies on bias and
  gradient differences carried from neighbouring levels by the smoothing
  steps.
- **S5 below 400 m:** the raw GLORYS profile lacks the warm modified
  Circumpolar Deep Water (−0.80 °C at 454 m, where the CTD measures 1.22 °C).
  At depth the bias term removes only 35 % of the bias, so the corrected
  profile remains too cold there (−0.08 °C at 454 m).

## Methods

Quality control, 1 m median binning, Savitzky–Golay smoothing, TEOS-10
conversion (GSW), interpolation onto the GLORYS levels, and the adaptive
bias and structural correction modulated by N² and the Turner angle. Full
description: the associated article and `docs/method.md` in the software
repository, which provides MATLAB and Python implementations that give the
same results. The corrected profiles were produced with the software version
cited above and reproduce the metrics table of the article to within its
two-decimal rounding.

## Licence and attribution

TODO (first author): licence of this record (proposed: CC-BY-4.0 for the CTD
data and corrected profiles).

The GLORYS extracts and the corrected profiles derive from a Copernicus Marine
Service product and remain subject to the Copernicus Marine Licence Agreement,
which permits redistribution with acknowledgement:

- `glorys/` (redistributed information): "E.U. Copernicus Marine Service
  Information; https://doi.org/10.48670/moi-00021".
- `corrected/` (derived product): "Generated using E.U. Copernicus Marine
  Service Information; https://doi.org/10.48670/moi-00021".

Product citation: Global Ocean Physics Reanalysis. E.U. Copernicus Marine
Service Information (CMEMS). Marine Data Store (MDS).
https://doi.org/10.48670/moi-00021 (Accessed on 14 February 2026).

## How to cite

TODO: dataset citation with the DOI assigned by Zenodo.
