"""Tests of the Sea-Bird .cnv reader."""

from pathlib import Path

import numpy as np

from glorys_correction.cnv import read_cnv

CTD = Path(__file__).resolve().parents[2] / "data" / "raw" / "ctd"


def test_reads_channels_and_signed_position():
    d = read_cnv(CTD / "NF003_008.cnv")
    assert list(d.columns) == ["depSM", "tv290C", "sal00", "c0S_m", "flag"]
    assert d.depSM.size == 1482                                   # header: nvalues
    np.testing.assert_allclose(d.latitude, -(68 + 9.73 / 60))     # 68 09.73 S
    np.testing.assert_allclose(d.longitude, -(69 + 32.12 / 60))   # 069 32.12 W
    np.testing.assert_allclose(d.depSM[:2], [-0.830, -0.829])


def test_all_casts_have_a_position_and_no_bad_flags():
    for f in sorted(CTD.glob("NF003_0*.cnv")):
        d = read_cnv(f)
        assert -70 < d.latitude < -67 and -71 < d.longitude < -67, f.name
        assert not np.isnan(d.depSM).any(), f.name
