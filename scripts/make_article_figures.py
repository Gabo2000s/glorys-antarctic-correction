"""Figures 2 and 3 of the associated article, from the corrected profiles.

    python scripts/make_article_figures.py [--profiles results/profiles] [--out results/figures]

* Figure 2 (``article_fig2_profiles.png``): CTD, raw GLORYS and corrected
  GLORYS profiles of Absolute Salinity and Conservative Temperature at the six
  stations, 2 x 6 panels.
* Figure 3 (``article_fig3_ts.png``): SA-Theta diagrams of the CTD (coloured
  by depth) and the corrected GLORYS profile (black) at the six stations, with
  sigma-0 isopycnals and the water-mass boxes, 2 x 3 panels and one colour bar.

Requires the glorys_correction package (``pip install -e python``).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from glorys_correction import STATIONS  # noqa: E402
from glorys_correction.figures import (GREY, ISOPYCNALS, WATER_MASSES, XLIM_TS,  # noqa: E402
                                       YLIM_TS, _isopycnal_grid)

ROOT = Path(__file__).resolve().parents[1]
DEPTH_MAX = 650.0             # colour-bar range of Figure 3 (m)


def read_profiles(folder: Path) -> dict:
    return {st.key: pd.read_csv(folder / f"{st.cast}_corrected_profile.csv") for st in STATIONS}


def figure_profiles(profiles: dict):
    """Figure 2: salinity and temperature panels of S1-S3 (top) and S4-S6 (bottom)."""
    fig, axs = plt.subplots(2, 6, figsize=(24, 10))
    for k, st in enumerate(STATIONS):
        df = profiles[st.key]
        r, c = divmod(k, 3)
        z = -df.depth_m
        for ax, var, xlabel, name in (
            (axs[r, 2 * c], "SA", "Absolute Salinity (g kg$^{-1}$)", "Salinity"),
            (axs[r, 2 * c + 1], "CT", "Conservative Temperature (°C)", "Temperature"),
        ):
            u = "gkg" if var == "SA" else "degC"
            ax.plot(df[f"{var}_ctd_{u}"], z, "k", lw=2, label="CTD")
            ax.plot(df[f"{var}_glorys_raw_{u}"], z, "--r", lw=1.5, label="GLORYS raw")
            ax.plot(df[f"{var}_glorys_corrected_{u}"], z, "b", lw=2, label="GLORYS corrected")
            ax.set_ylim(-700, 0)
            ax.set_xlabel(xlabel)
            ax.set_ylabel("Depth (m)")
            ax.set_title(f"{name}, {st.label}", fontweight="bold")
            ax.legend(loc="best", fontsize=8)
            ax.grid(True)
    fig.tight_layout()
    return fig


def figure_ts(profiles: dict):
    """Figure 3: SA-Theta diagrams, CTD coloured by depth and corrected GLORYS in black."""
    fig, axs = plt.subplots(2, 3, figsize=(18, 11), layout="constrained")
    cmap = plt.get_cmap("jet").reversed()
    norm = Normalize(0.0, DEPTH_MAX)
    for ax, st in zip(axs.flat, STATIONS):
        df = profiles[st.key]
        sc = ax.scatter(df.SA_ctd_gkg, df.CT_ctd_degC, c=df.depth_m, cmap=cmap, norm=norm,
                        marker="o", zorder=3)
        ax.scatter(df.SA_glorys_corrected_gkg, df.CT_glorys_corrected_degC, color="k",
                   marker="o", zorder=3)

        sa = pd.concat([df.SA_ctd_gkg, df.SA_glorys_corrected_gkg]).to_numpy()
        ct = pd.concat([df.CT_ctd_degC, df.CT_glorys_corrected_degC]).to_numpy()
        SA, T, sig = _isopycnal_grid(sa, ct)
        cs = ax.contour(SA, T, sig, levels=ISOPYCNALS, linestyles=":", colors=[GREY])
        ax.clabel(cs, fontsize=10, colors=[GREY])

        for name, (x0, x1), (y0, y1), colour, (tx, ty) in WATER_MASSES:
            ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=colour,
                                       alpha=0.1, edgecolor=colour, zorder=1))
            ax.text(tx, ty, name, color=colour, fontweight="bold", fontsize=12, zorder=4)

        ax.set_xlim(*XLIM_TS)
        ax.set_ylim(*YLIM_TS)
        ax.set_xlabel("SA (g kg$^{-1}$)", fontweight="bold")
        ax.set_ylabel("Conservative Temperature (°C)", fontweight="bold")
        ax.set_title(st.label, fontsize=13)
    fig.legend(handles=[
        Line2D([], [], ls="", marker="o", ms=9, mfc=cmap(0.15), mec=cmap(0.85),
               label="CTD (colour = depth)"),
        Line2D([], [], ls="", marker="o", ms=9, color="k", label="GLORYS corrected"),
    ], loc="outside lower center", ncol=2, fontsize=13, frameon=False)
    cb = fig.colorbar(sc, ax=axs, shrink=0.8)
    cb.set_label("Depth (m)", fontsize=13, fontweight="bold")
    cb.ax.invert_yaxis()
    return fig


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--profiles", type=Path, default=ROOT / "results" / "profiles")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "figures")
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args(argv)

    profiles = read_profiles(args.profiles)
    args.out.mkdir(parents=True, exist_ok=True)
    for fig, name in ((figure_profiles(profiles), "article_fig2_profiles.png"),
                      (figure_ts(profiles), "article_fig3_ts.png")):
        fig.savefig(args.out / name, dpi=args.dpi)
        plt.close(fig)
        print(f"Written {args.out / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
