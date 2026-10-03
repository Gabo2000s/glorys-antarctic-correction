# Changelog

All notable changes to this project are documented here. Versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.0] – 2026-10-02

Version used for the results of the associated article.

### Added

- Adaptive thermodynamic correction of GLORYS12V1 profiles against CTD casts,
  in MATLAB (`matlab/`) and Python (`python/`, package `glorys_correction`),
  with the same steps, function names and output formats. Temperatures are
  TEOS-10 Conservative Temperature: the CTD in-situ temperature and the
  GLORYS potential temperature are both converted to it. Corrected values
  are set to missing where GLORYS has no data (below the model seabed), so
  metrics before and after correction use the same levels.
- Sea-Bird `.cnv` readers, station list, figures (vertical profiles and T–S
  diagrams) and a run script for the six stations in both implementations.
- Input data: six CTD casts (cruise NF003, RV *Noosfera*, December 2025) and
  GLORYS12V1 station profiles, with checksums and station metadata.
- Results of the article: metrics, corrected profiles and figures
  (`results/`).
- Tests in both implementations against the article's metrics table and
  `results/metrics.csv`, and a check that the GLORYS temperature is read as
  potential temperature.
- `scripts/extract_glorys.py` to regenerate the GLORYS12V1 station profiles
  from the source NetCDF file (reproduces the published inputs),
  `scripts/compare_implementations.py` to compare two runs,
  `scripts/build_data_package.py` to assemble the Zenodo dataset record, and
  `scripts/make_article_figures.py` to draw Figures 2 and 3 of the article.
- Documentation of the method, the numerical definitions and the output
  formats.
- Licences: MIT for the code (`LICENSE`); CC BY 4.0 for the CTD casts, the
  station metadata and the corrected profiles; the GLORYS12V1 station
  profiles stay under the Copernicus Marine Service licence.
