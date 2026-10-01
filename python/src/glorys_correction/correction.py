"""Adaptive thermodynamic correction of GLORYS12V1 profiles at a CTD station.

The correction combines a depth-weighted bias term and a
stratification-weighted structural term, with an additional adjustment where
the Turner angle indicates diffusive convection. Step numbers in the comments
follow ``docs/method.md``.

Temperatures are Conservative Temperature (Theta, degC) and salinities
Absolute Salinity (g kg-1), the TEOS-10 variables. The CTD in-situ temperature
and the GLORYS potential temperature are both converted to Theta, which is
conserved when water masses mix and is the temperature that the TEOS-10
functions used here (sigma0, alpha, beta) take.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import gsw
import numpy as np
import pandas as pd
from scipy.interpolate import Akima1DInterpolator

from . import numerics as nm
from .cnv import read_cnv
from .stations import STATIONS, Station

# --- Parameters --------------------------------------------------------------
MIN_DEPTH = 0.5               # step 2: shallower samples are discarded (m)
DZ = 1.0                      # step 3: vertical bin size (m)
SGOLAY_CTD = 9                # step 5: Savitzky-Golay window (bins)
MOVMEDIAN_BIAS = 7            # step 11: moving-median window (levels)
MOVMEAN_GRAD = 7              # step 13: moving-mean window (levels)
G = 9.81                      # step 14: gravitational acceleration (m s-2)
RHO0 = 1027.0                 # step 14: reference density (kg m-3)
L_SURFACE = 80.0              # step 15: e-folding depth of the surface weight (m)
A_BIAS, B_BIAS = 0.92, 0.35   # step 16: bias factor = A * w_surface + B
KT, KS = 4.0, 2.0             # step 17: relaxation lengths for Theta and SA (m)
TU_LO, TU_HI = -90.0, -45.0   # step 19: diffusive-convection range (deg)
F_DD = 0.08                   # step 19: additional bias fraction
SGOLAY_FINAL = 7              # step 20: Savitzky-Golay window (levels)
OUTLIER_WINDOW = 5            # step 21: outlier window (levels)

METRIC_NAMES = (
    "bias_T_before", "bias_T_after", "bias_S_before", "bias_S_after",
    "rmse_T_before", "rmse_T_after", "rmse_S_before", "rmse_S_after",
    "corr_T_before", "corr_T_after", "corr_S_before", "corr_S_after",
)


@dataclass
class StationResult:
    """Profiles on the GLORYS levels, diagnostics and metrics for one station."""

    station: Station
    latitude: float
    longitude: float
    depth: np.ndarray
    pressure: np.ndarray
    SA_ctd: np.ndarray
    CT_ctd: np.ndarray
    SA_raw: np.ndarray
    CT_raw: np.ndarray
    SA_corrected: np.ndarray
    CT_corrected: np.ndarray
    bias_T: np.ndarray
    bias_S: np.ndarray
    N2: np.ndarray
    w_surface: np.ndarray
    w_structure: np.ndarray
    turner_angle: np.ndarray
    diffusive_mask: np.ndarray
    metrics: dict = field(default_factory=dict)

    def profile_table(self) -> pd.DataFrame:
        """Profiles on the GLORYS levels, one row per level."""
        return pd.DataFrame({
            "depth_m": self.depth,
            "pressure_dbar": self.pressure,
            "SA_ctd_gkg": self.SA_ctd,
            "CT_ctd_degC": self.CT_ctd,
            "SA_glorys_raw_gkg": self.SA_raw,
            "CT_glorys_raw_degC": self.CT_raw,
            "SA_glorys_corrected_gkg": self.SA_corrected,
            "CT_glorys_corrected_degC": self.CT_corrected,
            "N2_s-2": self.N2,
            "turner_angle_deg": self.turner_angle,
            "w_surface": self.w_surface,
            "w_structure": self.w_structure,
            "diffusive_convection": self.diffusive_mask.astype(int),
        })


def _makima(x, y, xq):
    """Modified Akima interpolation; NaN outside the range of ``x``."""
    f = Akima1DInterpolator(np.asarray(x, float), np.asarray(y, float),
                            method="makima", extrapolate=False)
    return f(np.asarray(xq, float))


def _rmse(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    return float(np.sqrt(np.nanmean(d ** 2)))


def correct_station(station: Station | int, data_dir: str | Path) -> StationResult:
    """Correct the GLORYS profile at one station.

    Parameters
    ----------
    station : Station or int
        A ``Station`` from ``STATIONS`` or its 0-based index.
    data_dir : path
        Folder containing the ``ctd/`` and ``glorys/`` sub-folders.
    """
    st = STATIONS[station] if isinstance(station, int) else station
    data_dir = Path(data_dir)

    # 1. Read the CTD cast ---------------------------------------------------
    ctd = read_cnv(st.ctd_path(data_dir))
    depth_ctd = np.asarray(ctd.depSM, dtype=float)
    t_ctd = np.asarray(ctd.tv290C, dtype=float)
    sp_ctd = np.asarray(ctd.sal00, dtype=float)
    lat, lon = ctd.latitude, ctd.longitude

    # 2. Quality control: valid samples, below 0.5 m, downcast only ----------
    keep = ~np.isnan(depth_ctd) & ~np.isnan(t_ctd) & ~np.isnan(sp_ctd)
    depth_ctd, t_ctd, sp_ctd = depth_ctd[keep], t_ctd[keep], sp_ctd[keep]
    keep = depth_ctd >= MIN_DEPTH
    depth_ctd, t_ctd, sp_ctd = depth_ctd[keep], t_ctd[keep], sp_ctd[keep]
    keep = np.concatenate(([True], np.diff(depth_ctd) > 0))
    depth_ctd, t_ctd, sp_ctd = depth_ctd[keep], t_ctd[keep], sp_ctd[keep]

    # 3. Median in 1 m bins --------------------------------------------------
    depth_bin, T_bin = nm.bin_median(depth_ctd, t_ctd, DZ)
    _, S_bin = nm.bin_median(depth_ctd, sp_ctd, DZ)

    # 4. Drop empty bins -----------------------------------------------------
    ok = ~np.isnan(T_bin) & ~np.isnan(S_bin)
    depth_bin, T_bin, S_bin = depth_bin[ok], T_bin[ok], S_bin[ok]

    # 5. Savitzky-Golay smoothing --------------------------------------------
    T_bin = nm.savgol_smooth(T_bin, SGOLAY_CTD)
    S_bin = nm.savgol_smooth(S_bin, SGOLAY_CTD)

    # 6. TEOS-10 conversion of the CTD profile (in-situ temperature) ---------
    p_bin = gsw.p_from_z(-depth_bin, lat)
    SA_bin = gsw.SA_from_SP(S_bin, p_bin, lon, lat)
    CT_bin = gsw.CT_from_t(SA_bin, T_bin, p_bin)
    sigma0_bin = gsw.sigma0(SA_bin, CT_bin)

    # 7. Read the GLORYS profile (median at each level) ----------------------
    gl = pd.read_csv(st.glorys_path(data_dir))
    depth = gl["depth"].to_numpy(dtype=float)
    sp_raw = gl["salt_median"].to_numpy(dtype=float)
    theta_raw = gl["temp_median"].to_numpy(dtype=float)

    # 8. TEOS-10 conversion of the GLORYS profile (potential temperature) ---
    pressure = gsw.p_from_z(-depth, lat)
    SA_raw = gsw.SA_from_SP(sp_raw, pressure, lon, lat)
    CT_raw = gsw.CT_from_pt(SA_raw, theta_raw)

    # 9. CTD interpolated onto the GLORYS levels -----------------------------
    CT_ctd = _makima(depth_bin, CT_bin, depth)
    SA_ctd = _makima(depth_bin, SA_bin, depth)

    # 10-11. Bias (GLORYS minus CTD), smoothed with a moving median ----------
    bias_T = nm.moving_median(CT_raw - CT_ctd, MOVMEDIAN_BIAS)
    bias_S = nm.moving_median(SA_raw - SA_ctd, MOVMEDIAN_BIAS)

    # 12. Vertical gradients -------------------------------------------------
    dTdz_ctd = nm.centred_gradient(CT_ctd, depth)
    dSdz_ctd = nm.centred_gradient(SA_ctd, depth)
    dTdz_raw = nm.centred_gradient(CT_raw, depth)
    dSdz_raw = nm.centred_gradient(SA_raw, depth)

    # 13. Structural bias, smoothed with a moving mean -----------------------
    grad_bias_T = nm.moving_mean(dTdz_raw - dTdz_ctd, MOVMEAN_GRAD)
    grad_bias_S = nm.moving_mean(dSdz_raw - dSdz_ctd, MOVMEAN_GRAD)

    # 14. Stratification N2 from the CTD (negative values set to zero) -------
    sigma0_ctd = _makima(depth_bin, sigma0_bin, depth)
    N2 = -(G / RHO0) * nm.centred_gradient(sigma0_ctd, depth)
    with np.errstate(invalid="ignore"):
        N2[N2 < 0] = 0.0

    # 15. Adaptive weights ---------------------------------------------------
    w_surface = np.exp(-depth / L_SURFACE)
    with np.errstate(invalid="ignore", divide="ignore"):
        w_structure = N2 / np.nanmax(N2)
    w_structure[np.isnan(w_structure)] = 0.0

    # 16. Bias term: factor 1.27 at the surface, tending to 0.35 at depth ----
    factor = A_BIAS * w_surface + B_BIAS
    CT_corr = CT_raw - factor * bias_T
    SA_corr = SA_raw - factor * bias_S

    # 17. Structural term ----------------------------------------------------
    CT_corr = CT_corr - KT * w_structure * grad_bias_T
    SA_corr = SA_corr - KS * w_structure * grad_bias_S

    # 18. Turner angle from the CTD ------------------------------------------
    alpha = gsw.alpha(SA_ctd, CT_ctd, pressure)
    beta = gsw.beta(SA_ctd, CT_ctd, pressure)
    turner = np.degrees(np.arctan2(alpha * dTdz_ctd + beta * dSdz_ctd,
                                   alpha * dTdz_ctd - beta * dSdz_ctd))

    # 19. Additional adjustment in the diffusive-convection regime -----------
    with np.errstate(invalid="ignore"):
        dd = (turner > TU_LO) & (turner < TU_HI)
    CT_corr[dd] = CT_corr[dd] - F_DD * bias_T[dd]
    SA_corr[dd] = SA_corr[dd] - F_DD * bias_S[dd]

    # 20. Final Savitzky-Golay smoothing -------------------------------------
    CT_corr = nm.savgol_smooth(CT_corr, SGOLAY_FINAL)
    SA_corr = nm.savgol_smooth(SA_corr, SGOLAY_FINAL)

    # 21. Outlier replacement; levels without GLORYS data set to missing -----
    CT_corr = nm.fill_outliers(CT_corr, OUTLIER_WINDOW)
    SA_corr = nm.fill_outliers(SA_corr, OUTLIER_WINDOW)
    CT_corr[np.isnan(CT_raw)] = np.nan
    SA_corr[np.isnan(SA_raw)] = np.nan

    # 22. Metrics, GLORYS minus CTD, before and after correction -------------
    metrics = {
        "bias_T_before": float(np.nanmean(CT_raw - CT_ctd)),
        "bias_T_after": float(np.nanmean(CT_corr - CT_ctd)),
        "bias_S_before": float(np.nanmean(SA_raw - SA_ctd)),
        "bias_S_after": float(np.nanmean(SA_corr - SA_ctd)),
        "rmse_T_before": _rmse(CT_raw, CT_ctd),
        "rmse_T_after": _rmse(CT_corr, CT_ctd),
        "rmse_S_before": _rmse(SA_raw, SA_ctd),
        "rmse_S_after": _rmse(SA_corr, SA_ctd),
        "corr_T_before": nm.pearson_r(CT_raw, CT_ctd),
        "corr_T_after": nm.pearson_r(CT_corr, CT_ctd),
        "corr_S_before": nm.pearson_r(SA_raw, SA_ctd),
        "corr_S_after": nm.pearson_r(SA_corr, SA_ctd),
    }

    return StationResult(
        station=st, latitude=lat, longitude=lon, depth=depth,
        pressure=pressure, SA_ctd=SA_ctd, CT_ctd=CT_ctd, SA_raw=SA_raw,
        CT_raw=CT_raw, SA_corrected=SA_corr, CT_corrected=CT_corr,
        bias_T=bias_T, bias_S=bias_S, N2=N2, w_surface=w_surface,
        w_structure=w_structure, turner_angle=turner, diffusive_mask=dd,
        metrics=metrics,
    )


def correct_all(data_dir: str | Path) -> list[StationResult]:
    """Correct the six stations."""
    return [correct_station(st, data_dir) for st in STATIONS]


def metrics_table(results: list[StationResult]) -> pd.DataFrame:
    """One row per station (S1..S6), one column per metric."""
    return pd.DataFrame({r.station.key: r.metrics for r in results}).T[list(METRIC_NAMES)]
