# MATLAB implementation

| File | Purpose |
|---|---|
| `run_correction.m` | Corrects the six stations and writes the outputs |
| `correct_station.m` | The correction for one station (steps 1–22 of `docs/method.md`) |
| `read_cnv.m` | Reads Sea-Bird `.cnv` files |
| `station_list.m` | Stations S1–S6 and their file names |
| `plot_profiles.m` | Vertical profiles figure |
| `plot_ts.m` | Temperature–salinity diagram |
| `tests/run_tests.m` | Checks against the published results |

## Requirements

- MATLAB R2019b or later (`interp1` with `'makima'`).
- [Gibbs SeaWater (GSW) Oceanographic Toolbox](https://www.teos-10.org/software.htm),
  version 3.06 or later, on the MATLAB path.

No other toolbox is needed.

## Usage

From this folder:

```matlab
run_correction                    % writes ../outputs/matlab/
run_correction([], true)          % also writes figures
run_correction('C:\some\folder')  % other output folder
```

`run_correction` prints a before → after summary per station and writes
`metrics.csv`, `summary.txt` and `profiles/` (formats in
[`../docs/outputs.md`](../docs/outputs.md)). It reads the inputs from
`../data/raw/`, so it works from any current folder.

To correct one station and inspect the result:

```matlab
stations = station_list();
res = correct_station(stations(1), fullfile('..', 'data', 'raw'));
res.metrics
plot_profiles(res);
plot_ts(res);
```

## Tests

```matlab
run tests/run_tests.m
```

The tests check the `.cnv` reader, the metrics against the article's metrics
table (printed with two decimals, tolerance 0.006) and against
`../results/metrics.csv` (tolerance 1e-6), and that the corrected profiles
are missing exactly where GLORYS has no data.
