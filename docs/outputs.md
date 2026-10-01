# Output formats

Both implementations write the same files with the same formats, so the
outputs of two runs can be compared directly with
`scripts/compare_implementations.py`. All text files use UTF-8 and LF line
endings.

## `metrics.csv`

One row per station, comma-separated, values with 15 significant digits.

| Column | Units | Description |
|---|---|---|
| `station` | – | S1 … S6 |
| `bias_T_before`, `bias_T_after` | °C | Mean of GLORYS minus CTD Conservative Temperature |
| `bias_S_before`, `bias_S_after` | g kg⁻¹ | Mean of GLORYS minus CTD Absolute Salinity |
| `rmse_T_before`, `rmse_T_after` | °C | Root-mean-square difference, Conservative Temperature |
| `rmse_S_before`, `rmse_S_after` | g kg⁻¹ | Root-mean-square difference, salinity |
| `corr_T_before`, `corr_T_after` | – | Pearson r, Conservative Temperature |
| `corr_S_before`, `corr_S_after` | – | Pearson r, salinity |

`before` is the raw GLORYS profile, `after` the corrected one. Statistics use
the GLORYS levels that have both GLORYS and CTD data, the same levels before
and after correction.

## `profiles/NF003_0XX_corrected_profile.csv`

One file per station, one row per GLORYS level, six decimals, missing values
written as `NaN`.

| Column | Units | Description |
|---|---|---|
| `depth_m` | m | GLORYS level depth |
| `pressure_dbar` | dbar | Sea pressure (TEOS-10) |
| `SA_ctd_gkg` | g kg⁻¹ | CTD Absolute Salinity on the GLORYS levels |
| `CT_ctd_degC` | °C | CTD Conservative Temperature on the GLORYS levels |
| `SA_glorys_raw_gkg` | g kg⁻¹ | GLORYS Absolute Salinity before correction |
| `CT_glorys_raw_degC` | °C | GLORYS Conservative Temperature before correction |
| `SA_glorys_corrected_gkg` | g kg⁻¹ | GLORYS Absolute Salinity after correction (`NaN` where GLORYS has no data) |
| `CT_glorys_corrected_degC` | °C | GLORYS Conservative Temperature after correction (`NaN` where GLORYS has no data) |
| `N2_s-2` | s⁻² | Buoyancy frequency squared from the CTD (negative values set to 0) |
| `turner_angle_deg` | ° | Turner angle from the CTD |
| `w_surface` | – | Surface weight, exp(−z / 80 m) |
| `w_structure` | – | Stratification weight, N² / max(N²) |
| `diffusive_convection` | 0/1 | 1 where −90° < Tu < −45° |

## `summary.txt`

The before → after metrics printed to the console, three lines per station:

```
S1  NF003_008  Station-01
  Temperature (degC)  bias   0.077 ->   0.165  RMSE  0.526 ->  0.277  r  0.822 ->  0.968
  Salinity (g/kg)     bias  -0.803 ->   0.141  RMSE  1.175 ->  0.210  r  0.921 ->  0.911
```

## `figures/` (optional)

`profiles_Station-0X.png`: CTD (black), raw GLORYS (red, dashed) and corrected
GLORYS (blue) against depth, for Absolute Salinity and Conservative Temperature.
`TS_Station-0X.png`: SA–Θ diagram with the CTD coloured by depth, the corrected
GLORYS profile in black, σ₀ isopycnals and the AASW, WW and mCDW boxes.
Figures are written at 300 dpi.
