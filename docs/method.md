# Method

The algorithm corrects GLORYS12V1 temperature and salinity profiles at a CTD
station so that they match the observed vertical structure while keeping the
signatures of the regional water masses: Antarctic Surface Water (AASW),
Winter Water (WW) and modified Circumpolar Deep Water (mCDW).

The steps below are implemented in `matlab/correct_station.m` and
`python/src/glorys_correction/correction.py`, which use the same step numbers.

## Steps

### CTD processing

1. Read the cast: depth, ITS-90 temperature, Practical Salinity and the NMEA
   position in the file header.
2. Quality control: drop missing values and samples shallower than 0.5 m, and
   keep the downcast only (each sample deeper than the previous one).
3. Bin into 1 m bins using the median.
4. Drop empty bins.
5. Smooth with a quadratic Savitzky–Golay filter over 9 bins.
6. Convert with TEOS-10: pressure, Absolute Salinity (SA), Conservative
   Temperature Θ (from the in-situ temperature) and σ₀ (from SA and Θ).

### GLORYS profile and common grid

7. Read the GLORYS station profile and use the median temperature and
   salinity at each level. The station profiles hold the daily mean of the
   day nearest to the cast, summarised over the 2 × 2 grid cells nearest to
   the station (`scripts/extract_glorys.py`, described in
   `data/DATASET_README.md`).
8. Convert with TEOS-10 at the CTD position: Practical to Absolute Salinity,
   and potential temperature (`thetao`) to Θ.
9. Interpolate the CTD Θ and SA onto the GLORYS levels (modified Akima, no
   extrapolation: levels outside the cast are missing).

### Diagnostics and weights

10. Bias: GLORYS minus CTD, for Θ and SA.
11. Smooth the bias with a 7-level moving median.
12. Vertical gradients of Θ and SA, for the CTD and for GLORYS.
13. Structural bias: GLORYS gradient minus CTD gradient, smoothed with a
    7-level moving mean.
14. Stratification from the CTD: N² = −(g/ρ₀) dσ₀/dz with g = 9.81 m s⁻² and
    ρ₀ = 1027 kg m⁻³; negative values are set to zero.
15. Weights: `w_surface = exp(−z / 80 m)` and `w_structure = N² / max(N²)`
    (zero where N² is missing).

### Correction

16. Bias term: `X = X_GLORYS − (0.92 w_surface + 0.35) · bias`. The factor is
    1.27 at the surface and tends to 0.35 at depth.
17. Structural term: `X = X − k · structural bias`, with
    `k = 4 m · w_structure` for Θ and `k = 2 m · w_structure` for SA. `k` is a
    relaxation length that is active only where the water column is
    stratified.
18. Turner angle from the CTD, with the thermal expansion and haline
    contraction coefficients α and β (TEOS-10, with respect to Θ and SA):
    `Tu = atan2(α dΘ/dz + β dSA/dz, α dΘ/dz − β dSA/dz)`.
19. Where −90° < Tu < −45° (diffusive convection: cold, fresh water above
    warm, salty water), subtract a further 8 % of the bias.
20. Smooth with a quadratic Savitzky–Golay filter over 7 levels.
21. Replace outliers (see below) over a 5-level window, then set the
    corrected values to missing at levels where GLORYS has no data (below the
    model seabed).

### Metrics

22. Bias (mean difference), root-mean-square error and Pearson correlation
    between GLORYS and the CTD, before and after correction, over the levels
    where both GLORYS and the CTD have data (the same levels before and
    after).

## Numerical definitions

Several operations admit variants that give different numbers. Both
implementations use the definitions below.

| Operation | Definition |
|---|---|
| Vertical gradient | Interior levels: `(f[i+1] − f[i−1]) / (z[i+1] − z[i−1])`; first and last level: one-sided first difference. GLORYS levels are non-uniform (about 1 m apart near the surface, about 100 m below 500 m). |
| 1 m bins | Bins `[k, k+1)` m from 0 to the next integer above the deepest sample; the last bin includes its upper edge. Bin value: median. |
| Savitzky–Golay | Least-squares quadratic over a window of `k` samples, evaluated at each sample. Near the ends the window keeps its length and is shifted against the end of the profile. |
| Moving median and mean | Centred window of `k` samples, truncated at the ends of the profile. Missing values are ignored, so a missing sample receives the statistic of its valid neighbours. |
| Missing values in smoothing | Ignored inside the window (steps 5, 11, 13, 20). |
| Outliers | A value is an outlier if it lies more than 3 scaled median absolute deviations (scale 1.4826) from the median of the centred 5-level window. Outliers are replaced by linear interpolation between the nearest non-outliers, with linear extrapolation at the ends. |
| Interpolation | Modified Akima (makima); no extrapolation. |
| Correlation | Pearson's r over levels where both profiles have values. |

## Notes

- **Temperature.** The correction works in Conservative Temperature Θ, the
  TEOS-10 temperature variable. Θ is proportional to potential enthalpy, so
  it is conserved when water masses mix; the bias, gradients, smoothing and
  interpolation are linear operations that treat temperature that way, and
  the TEOS-10 functions for σ₀, α and β take Θ. The CTD measures in-situ
  temperature (converted with `CT_from_t`); GLORYS provides potential
  temperature θ (converted with `CT_from_pt`, an exact conversion). In these
  profiles Θ and θ differ by up to 0.009 °C (CTD) and 0.026 °C (GLORYS).
- **Windows** in steps 11, 13, 20 and 21 are counted in GLORYS levels, not
  metres: a 7-level window spans a few metres near the surface and several
  hundred metres at depth.
- **Position.** The TEOS-10 conversions use the NMEA position stored in each
  CTD file header, which is the confirmed station position
  (`data/stations.csv`).
- **Gaps.** The smoothing steps ignore missing values, so they also produce
  values at levels where an input is missing. Step 21 removes them where
  GLORYS has no data. Where only the CTD is missing (the 0.5 m level and below
  the deepest sample) the corrected values are kept but are not validated; see
  "Known limitations" in `data/DATASET_README.md`.
