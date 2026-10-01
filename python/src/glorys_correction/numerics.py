"""Numerical operations used by the correction.

Each function implements one operation exactly as defined in the method
(``docs/method.md``, "Numerical definitions"). The definitions matter: for
example, vertical gradients use centred differences over the two neighbouring
levels, which on the strongly non-uniform GLORYS grid differs from
higher-order schemes.

None of these functions calls LAPACK or BLAS (``np.linalg``, ``np.polyfit``,
``np.corrcoef``), so the correction runs even where NumPy's linear algebra
library is unavailable.
"""

from __future__ import annotations

import numpy as np

#: Scale factor that makes the median absolute deviation a consistent
#: estimator of the standard deviation for normal data, 1 / Phi^-1(3/4).
MAD_SCALE = 1.482602218505602


def centred_gradient(f, x):
    """Derivative of ``f`` with respect to ``x`` on a possibly non-uniform grid.

    Interior points: ``(f[i+1] - f[i-1]) / (x[i+1] - x[i-1])``.
    End points: one-sided first differences.
    """
    f = np.asarray(f, dtype=float)
    x = np.asarray(x, dtype=float)
    n = f.size
    if n < 2:
        return np.full(n, np.nan)
    g = np.empty(n, dtype=float)
    g[0] = (f[1] - f[0]) / (x[1] - x[0])
    g[-1] = (f[-1] - f[-2]) / (x[-1] - x[-2])
    if n > 2:
        g[1:-1] = (f[2:] - f[:-2]) / (x[2:] - x[:-2])
    return g


def bin_median(z, values, dz):
    """Median of ``values`` in vertical bins of size ``dz`` starting at 0.

    Bins are ``[k dz, (k+1) dz)`` for ``k = 0 .. ceil(max(z)/dz) - 1``; the
    last bin is also closed on the right. Returns the bin centres and the
    median in each bin (NaN for empty bins). Samples outside the bins are
    ignored.
    """
    z = np.asarray(z, dtype=float)
    values = np.asarray(values, dtype=float)
    edges = np.arange(0.0, np.ceil(z.max()) + dz / 2, dz)
    centres = (edges[:-1] + edges[1:]) / 2.0
    nbins = centres.size

    k = np.digitize(z, edges, right=False) - 1
    k[z == edges[-1]] = nbins - 1
    inside = (z >= edges[0]) & (z <= edges[-1])

    out = np.full(nbins, np.nan)
    kk, vv = k[inside], values[inside]
    order = np.argsort(kk, kind="stable")
    kk, vv = kk[order], vv[order]
    cuts = np.flatnonzero(np.diff(kk)) + 1
    for grp, seg in zip(np.split(kk, cuts), np.split(vv, cuts)):
        if grp.size:
            out[grp[0]] = np.median(seg)
    return centres, out


def _window(i, n, k):
    """Centred window of ``k`` samples at index ``i``, truncated at the ends.

    For even ``k`` the window is ``[i - k/2, i + k/2 - 1]``.
    """
    if k % 2 == 1:
        lo, hi = i - (k - 1) // 2, i + (k - 1) // 2 + 1
    else:
        lo, hi = i - k // 2, i + k // 2
    return max(0, lo), min(n, hi)


def _moving(x, k, agg):
    x = np.asarray(x, dtype=float)
    n = x.size
    out = np.empty(n, dtype=float)
    for i in range(n):
        lo, hi = _window(i, n, k)
        w = x[lo:hi]
        w = w[~np.isnan(w)]
        out[i] = agg(w) if w.size else np.nan
    return out


def moving_median(x, k):
    """Centred moving median over ``k`` samples.

    The window is truncated at the ends of the profile. NaN values are
    ignored inside the window, so a NaN sample receives the median of its
    valid neighbours.
    """
    return _moving(x, k, np.median)


def moving_mean(x, k):
    """Centred moving mean over ``k`` samples (same window rules as
    :func:`moving_median`)."""
    return _moving(x, k, np.mean)


def _fit_at_zero(t, v, degree):
    """Least-squares polynomial of ``degree`` evaluated at ``t = 0``.

    Solves the normal equations (at most 3 x 3, abscissa centred on the
    evaluation point) by Gauss-Jordan elimination with partial pivoting.
    """
    n = degree + 1
    s = np.array([np.sum(t ** j) for j in range(2 * degree + 1)], dtype=float)
    b = np.array([np.sum((t ** j) * v) for j in range(n)], dtype=float)
    m = np.empty((n, n + 1), dtype=float)
    for r in range(n):
        for c in range(n):
            m[r, c] = s[r + c]
        m[r, n] = b[r]
    for col in range(n):
        piv = col + int(np.argmax(np.abs(m[col:, col])))
        if abs(m[piv, col]) < 1e-300:
            return np.nan
        if piv != col:
            m[[col, piv]] = m[[piv, col]]
        m[col] /= m[col, col]
        for r in range(n):
            if r != col and m[r, col] != 0.0:
                m[r] -= m[r, col] * m[col]
    return float(m[0, n])


def savgol_smooth(x, k, degree=2):
    """Savitzky-Golay smoothing with a window of ``k`` samples.

    At each sample a polynomial of ``degree`` is fitted by least squares to
    the ``k`` samples of the window and evaluated at that sample. Near the
    ends the window keeps its full length and is shifted against the end of
    the profile. NaN values are ignored in the fit.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    span = min(k, n)
    out = np.empty(n, dtype=float)
    for i in range(n):
        lo, hi = _window(i, n, k)
        if hi - lo < span:
            if lo == 0:
                hi = span
            else:
                lo = n - span
        t = np.arange(lo, hi, dtype=float) - i
        v = x[lo:hi]
        keep = ~np.isnan(v)
        t, v = t[keep], v[keep]
        out[i] = _fit_at_zero(t, v, min(degree, v.size - 1)) if v.size else np.nan
    return out


def fill_outliers(x, k=5, thresh=3.0):
    """Replace outliers by linear interpolation of their neighbours.

    A sample is an outlier when it lies more than ``thresh`` scaled median
    absolute deviations from the median of a centred window of ``k`` samples
    (truncated at the ends). Outliers are replaced by linear interpolation
    between the nearest non-outlier samples, with linear extrapolation at the
    ends of the profile. When the local MAD is zero, any deviation from the
    local median counts as an outlier.
    """
    x = np.asarray(x, dtype=float).copy()
    n = x.size
    is_out = np.zeros(n, dtype=bool)
    for i in range(n):
        if np.isnan(x[i]):
            continue
        lo, hi = _window(i, n, k)
        w = x[lo:hi]
        w = w[~np.isnan(w)]
        med = np.median(w)
        mad = MAD_SCALE * np.median(np.abs(w - med))
        is_out[i] = abs(x[i] - med) > thresh * mad

    good = ~is_out & ~np.isnan(x)
    if not is_out.any() or good.sum() < 2:
        return x

    xg = np.flatnonzero(good).astype(float)
    yg = x[good]
    xo = np.flatnonzero(is_out).astype(float)
    filled = np.interp(xo, xg, yg)
    left, right = xo < xg[0], xo > xg[-1]
    if left.any():
        slope = (yg[1] - yg[0]) / (xg[1] - xg[0])
        filled[left] = yg[0] + slope * (xo[left] - xg[0])
    if right.any():
        slope = (yg[-1] - yg[-2]) / (xg[-1] - xg[-2])
        filled[right] = yg[-1] + slope * (xo[right] - xg[-1])
    x[is_out] = filled
    return x


def pearson_r(a, b):
    """Pearson correlation of the pairs where both ``a`` and ``b`` are valid."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    keep = ~np.isnan(a) & ~np.isnan(b)
    if keep.sum() < 2:
        return np.nan
    da = a[keep] - a[keep].mean()
    db = b[keep] - b[keep].mean()
    den = np.sqrt(np.sum(da * da) * np.sum(db * db))
    return np.nan if den == 0 else float(np.sum(da * db) / den)
