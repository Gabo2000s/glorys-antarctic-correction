# Data

| Path | Content |
|---|---|
| `raw/ctd/NF003_0XX.cnv` | Six Sea-Bird CTD casts, Marguerite Bay, 11–15 Dec 2025, RV *Noosfera* cruise NF003 |
| `raw/glorys/GLORYS_Raw_Station_0XX.csv` | GLORYS12V1 statistics at each station (Copernicus Marine Service) |
| `stations.csv` | Confirmed station dates, positions and cast depths (and the manuscript's Table 1 values for reference) |
| `SHA256SUMS.txt` | Checksums of the raw files |
| `DATASET_README.md` | Description of the published dataset record |

The GLORYS files are regenerated from the source GLORYS12V1 NetCDF file (not
distributed here) with `scripts/extract_glorys.py`; the extraction method is
described in [`DATASET_README.md`](DATASET_README.md).

These are the inputs of the correction. The citable copy of the data, together
with the corrected profiles, is the Zenodo dataset record
(TODO: dataset DOI). The files here are byte-for-byte identical to that record;
`.gitattributes` stops git from changing their line endings, and
`scripts/build_data_package.py` checks them against `SHA256SUMS.txt` before
packaging.

Licences: CC BY 4.0 for the CTD casts and the station metadata; the GLORYS12V1
station profiles are E.U. Copernicus Marine Service Information
(https://doi.org/10.48670/moi-00021), redistributed under the Copernicus
Marine Service licence.

Variables, units, provenance, known metadata discrepancies and licences are
described in [`DATASET_README.md`](DATASET_README.md).
