"""Run the correction for the six stations.

    python -m glorys_correction                  # metrics, profiles, summary
    python -m glorys_correction --figures        # + figures
    python -m glorys_correction --data data/raw --out outputs/python

Run from the repository root. Outputs (format in ``docs/outputs.md``):

    <out>/metrics.csv
    <out>/summary.txt
    <out>/profiles/NF003_0XX_corrected_profile.csv
    <out>/figures/profiles_Station-0X.png, TS_Station-0X.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .correction import correct_all, metrics_table


def summary_block(res) -> str:
    """Before -> after metrics of one station, as printed to the console."""
    m = res.metrics
    st = res.station
    row = "  {:<19s} bias {:7.3f} -> {:7.3f}  RMSE {:6.3f} -> {:6.3f}  r {:6.3f} -> {:6.3f}"
    return "\n".join([
        f"{st.key}  {st.cast}  {st.label}",
        row.format("Temperature (degC)", m["bias_T_before"], m["bias_T_after"],
                   m["rmse_T_before"], m["rmse_T_after"],
                   m["corr_T_before"], m["corr_T_after"]),
        row.format("Salinity (g/kg)", m["bias_S_before"], m["bias_S_after"],
                   m["rmse_S_before"], m["rmse_S_after"],
                   m["corr_S_before"], m["corr_S_after"]),
    ])


def write_outputs(results, out: Path, figures: bool = False, dpi: int = 300) -> None:
    """Write metrics, profiles, summary and (optionally) figures to ``out``."""
    profiles_dir = out / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    table = metrics_table(results)
    table.index.name = "station"
    table.to_csv(out / "metrics.csv", float_format="%.15g", lineterminator="\n")

    for res in results:
        res.profile_table().to_csv(
            profiles_dir / f"{res.station.cast}_corrected_profile.csv",
            index=False, float_format="%.6f", na_rep="NaN", lineterminator="\n")

    summary = "\n\n".join(summary_block(r) for r in results) + "\n"
    (out / "summary.txt").write_text(summary, encoding="utf-8", newline="\n")

    if figures:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from .figures import plot_profiles, plot_ts
        fig_dir = out / "figures"
        for res in results:
            plt.close(plot_profiles(res, fig_dir, dpi=dpi))
            plt.close(plot_ts(res, fig_dir, dpi=dpi))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m glorys_correction",
                                 description="Correct GLORYS12V1 profiles against CTD casts.")
    ap.add_argument("--data", type=Path, default=Path("data") / "raw",
                    help="folder with ctd/ and glorys/ (default: data/raw)")
    ap.add_argument("--out", type=Path, default=Path("outputs") / "python",
                    help="output folder (default: outputs/python)")
    ap.add_argument("--figures", action="store_true", help="also write PNG figures")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)

    results = correct_all(args.data)
    for res in results:
        print(summary_block(res) + "\n")
    write_outputs(results, args.out, figures=args.figures, dpi=args.dpi)
    print(f"Outputs written to {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
