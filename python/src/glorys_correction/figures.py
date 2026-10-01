"""Figures: vertical profiles and temperature-salinity diagrams.

``plot_profiles`` draws the CTD, raw GLORYS and corrected GLORYS profiles;
``plot_ts`` draws the temperature-salinity diagram with sigma-0 isopycnals
and the boxes of the regional water masses.
"""

from __future__ import annotations

from pathlib import Path

import gsw
import matplotlib.pyplot as plt
import numpy as np

from .correction import StationResult

ISOPYCNALS = np.arange(23.0, 40.0 + 1e-9, 0.5)
P_REF = 0.0
SA_MIN, T_MIN = 22.0, -2.0
XLIM_TS, YLIM_TS = (32.5, 35.0), (-1.6, 1.6)
GREY = (0.5, 0.5, 0.5)

# Water masses: Antarctic Surface Water, Winter Water, modified Circumpolar
# Deep Water. name, (SA min, SA max), (Theta min, Theta max), colour, label position
WATER_MASSES = (
    ("AASW", (33.0, 34.29), (0.0, 1.6), "g", (33.6, 1.2)),
    ("WW", (33.4, 34.4), (-1.9, 0.0), "b", (34.2, -1.25)),
    ("mCDW", (34.3, 35.0), (0.0, 1.6), "r", (34.7, 0.43)),
)


def plot_profiles(res: StationResult, outdir: str | Path | None = None,
                  dpi: int = 300):
    """Absolute Salinity and Conservative Temperature against depth."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 6))
    z = -res.depth
    for ax, ctd, raw, cor, xlabel, title in (
        (ax1, res.SA_ctd, res.SA_raw, res.SA_corrected,
         "Absolute Salinity (g kg$^{-1}$)", "Salinity"),
        (ax2, res.CT_ctd, res.CT_raw, res.CT_corrected,
         "Conservative Temperature (°C)", "Temperature"),
    ):
        ax.plot(ctd, z, "k", lw=2, label="CTD")
        ax.plot(raw, z, "--r", lw=1.5, label="GLORYS raw")
        ax.plot(cor, z, "b", lw=2, label="GLORYS corrected")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Depth (m)")
        ax.set_title(f"{title} {res.station.label} ({res.station.cast})")
        ax.legend(loc="best")
        ax.grid(True)
    fig.tight_layout()
    if outdir is not None:
        Path(outdir).mkdir(parents=True, exist_ok=True)
        fig.savefig(Path(outdir) / f"profiles_{res.station.label}.png", dpi=dpi)
    return fig


def _isopycnal_grid(sa, t):
    sa_max = np.nanmax(sa) + 0.1 * (np.nanmax(sa) - np.nanmin(sa))
    t_max = np.nanmax(t) + 0.1 * (np.nanmax(t) - np.nanmin(t))
    sa_axis = np.arange(SA_MIN, sa_max + 1e-12, (sa_max - SA_MIN) / 600.0)
    t_axis = np.arange(T_MIN, t_max + 1e-12, (t_max - T_MIN) / 200.0)
    SA, T = np.meshgrid(sa_axis, t_axis)
    return SA, T, gsw.rho(SA, T, P_REF) - 1000.0


def plot_ts(res: StationResult, outdir: str | Path | None = None, dpi: int = 300):
    """Temperature-salinity diagram: CTD coloured by depth, corrected GLORYS
    in black, with sigma-0 isopycnals and water-mass boxes."""
    fig, ax = plt.subplots(figsize=(8.5, 8.5), facecolor="w")
    cmap = plt.get_cmap("jet").reversed()
    sc = ax.scatter(res.SA_ctd, res.CT_ctd, c=res.depth, cmap=cmap,
                    marker="o", zorder=3, label="CTD")
    ax.scatter(res.SA_corrected, res.CT_corrected, color="k", marker="o",
               zorder=3, label="GLORYS corrected")

    SA, T, sig = _isopycnal_grid(res.SA_ctd, res.CT_ctd)
    cs = ax.contour(SA, T, sig, levels=ISOPYCNALS, linestyles=":", colors=[GREY])
    ax.clabel(cs, fontsize=14, colors=[GREY])
    SA, T, sig = _isopycnal_grid(res.SA_corrected, res.CT_corrected)
    cs = ax.contour(SA, T, sig, linestyles=":", colors=[GREY])
    ax.clabel(cs, fontsize=14, colors=[GREY])

    for name, (x0, x1), (y0, y1), colour, (tx, ty) in WATER_MASSES:
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=colour,
                                   alpha=0.1, edgecolor=colour, zorder=1))
        ax.text(tx, ty, name, color=colour, fontweight="bold", fontsize=14, zorder=4)

    cb = fig.colorbar(sc, ax=ax)
    cb.set_label("Depth (m)")
    cb.ax.invert_yaxis()
    ax.set_xlim(*XLIM_TS)
    ax.set_ylim(*YLIM_TS)
    ax.set_xlabel("SA (g kg$^{-1}$)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Conservative Temperature (°C)", fontsize=14, fontweight="bold")
    ax.set_title(res.station.label, fontsize=14)
    ax.tick_params(labelsize=14)
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([], [], ls="", marker="o", mfc=cmap(0.15), mec=cmap(0.85),
               label="CTD (colour = depth)"),
        Line2D([], [], ls="", marker="o", color="k", label="GLORYS corrected"),
    ], loc="lower right")
    for s in ax.spines.values():
        s.set_linewidth(1.5)
    ax.set_box_aspect(1)
    fig.tight_layout()
    if outdir is not None:
        Path(outdir).mkdir(parents=True, exist_ok=True)
        fig.savefig(Path(outdir) / f"TS_{res.station.label}.png", dpi=dpi)
    return fig
