# Python implementation

Package `glorys_correction`.

| Module | Purpose |
|---|---|
| `__main__.py` | Corrects the six stations and writes the outputs (`python -m glorys_correction`) |
| `correction.py` | The correction for one station (steps 1–22 of `docs/method.md`) |
| `numerics.py` | Numerical operations (gradient, binning, smoothing, outliers, correlation) |
| `cnv.py` | Reads Sea-Bird `.cnv` files |
| `stations.py` | Stations S1–S6 and their file names |
| `figures.py` | Vertical profiles and temperature–salinity diagrams |

## Requirements

Python 3.10 or later with numpy, scipy (≥ 1.13), pandas, matplotlib and
[gsw](https://teos-10.github.io/GSW-Python/).

## Installation

With [Miniforge](https://github.com/conda-forge/miniforge), from the
repository root (Windows: *Miniforge Prompt*):

```bash
conda env create -f python/environment.yml
conda activate glorys-correction
pip install -e python
```

## Usage

From the repository root:

```bash
python -m glorys_correction                       # writes outputs/python/
python -m glorys_correction --figures             # also writes figures
python -m glorys_correction --out some/folder
```

The command prints a before → after summary per station and writes
`metrics.csv`, `summary.txt` and `profiles/` (formats in
[`../docs/outputs.md`](../docs/outputs.md)).

To correct one station and inspect the result:

```python
from glorys_correction import STATIONS, correct_station
from glorys_correction.figures import plot_profiles, plot_ts

res = correct_station(STATIONS[0], "data/raw")   # S1, cast NF003_008
res.metrics["rmse_S_after"]                      # g/kg
res.profile_table()                              # pandas DataFrame
plot_profiles(res)
plot_ts(res)
```

## Tests

```bash
pip install -e "python[test]"
pytest python
```

The tests check the `.cnv` reader, the numerical operations against
hand-computed values, and the metrics against the article's metrics table
(printed with two decimals, tolerance 0.006) and against
`../results/metrics.csv` (tolerance 1e-9). They also check that the corrected
profiles are missing exactly where GLORYS has no data and that the metrics
before and after correction use the same levels.
