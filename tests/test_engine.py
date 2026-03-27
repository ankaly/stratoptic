"""
TMM Engine tests — energy conservation, physical laws, edge cases.
"""

import numpy as np
import pytest

from motor.engine import TMMEngine, Structure, Layer
from motor.rii_db import RIIDatabase

DB_ROOT = __import__("os").path.join(__import__("os").path.dirname(__file__),
                                     "..", "data", "rii_db")

WLS = np.linspace(400, 800, 40)  # nm, coarser for speed


def _make_db():
    return RIIDatabase(DB_ROOT)


# ---------------------------------------------------------------------------
# test_air_only
# ---------------------------------------------------------------------------

def test_air_only():
    """No film layers, incident=air, substrate=air → R≈0, T≈1."""
    db = _make_db()
    air = db.get("Air")
    st = Structure(layers=[], incident=air, substrate=air,
                   substrate_coherent=True)
    res = TMMEngine(st).calculate(WLS, angle=0.0, polarization="s")
    assert np.allclose(res.R, 0.0, atol=1e-6), "R should be ~0 for air/air"
    assert np.allclose(res.T, 1.0, atol=1e-6), "T should be ~1 for air/air"


# ---------------------------------------------------------------------------
# test_single_dielectric
# ---------------------------------------------------------------------------

def test_single_dielectric():
    """SiO2 film on BK7 — R+T+A must equal 1."""
    db = _make_db()
    sio2 = db.get("SiO2")
    bk7 = db.get("Glass_BK7")
    air = db.get("Air")
    st = Structure(layers=[Layer(sio2, 100.0)], incident=air, substrate=bk7,
                   substrate_coherent=True)
    res = TMMEngine(st).calculate(WLS, polarization="s")
    total = res.R + res.T + res.A
    assert np.allclose(total, 1.0, atol=1e-6), f"R+T+A not 1: max dev={np.abs(total-1).max()}"


# ---------------------------------------------------------------------------
# test_metal_film
# ---------------------------------------------------------------------------

def test_metal_film():
    """50 nm Ag film → high reflectance (>50%) across visible."""
    db = _make_db()
    ag = db.get("Ag")
    air = db.get("Air")
    bk7 = db.get("Glass_BK7")
    st = Structure(layers=[Layer(ag, 50.0)], incident=air, substrate=bk7,
                   substrate_coherent=True)
    res = TMMEngine(st).calculate(WLS, polarization="s")
    assert res.R.mean() > 0.5, f"Ag R mean={res.R.mean():.3f}, expected >0.5"


# ---------------------------------------------------------------------------
# test_unpolarized
# ---------------------------------------------------------------------------

def test_unpolarized():
    """Unpolarized result should equal average of s and p."""
    db = _make_db()
    sio2 = db.get("SiO2")
    air = db.get("Air")
    bk7 = db.get("Glass_BK7")
    st = Structure(layers=[Layer(sio2, 200.0)], incident=air, substrate=bk7,
                   substrate_coherent=True)
    eng = TMMEngine(st)
    angle = 30.0
    res_s = eng.calculate(WLS, angle=angle, polarization="s")
    res_p = eng.calculate(WLS, angle=angle, polarization="p")
    res_u = eng.calculate(WLS, angle=angle, polarization="unpolarized")
    expected_R = (res_s.R + res_p.R) / 2.0
    assert np.allclose(res_u.R, expected_R, atol=1e-9), "Unpolarized R != (R_s+R_p)/2"


# ---------------------------------------------------------------------------
# test_angle_dependence
# ---------------------------------------------------------------------------

def test_angle_dependence():
    """Reflectance at 45° should differ from normal incidence."""
    db = _make_db()
    bk7 = db.get("Glass_BK7")
    air = db.get("Air")
    st = Structure(layers=[], incident=air, substrate=bk7,
                   substrate_coherent=True)
    eng = TMMEngine(st)
    res0 = eng.calculate(WLS, angle=0.0, polarization="s")
    res45 = eng.calculate(WLS, angle=45.0, polarization="s")
    assert not np.allclose(res0.R, res45.R, atol=1e-3), \
        "R at 0° and 45° should differ"


# ---------------------------------------------------------------------------
# test_energy_conservation
# ---------------------------------------------------------------------------

def test_energy_conservation():
    """R + T + A = 1 for every wavelength and scenario."""
    db = _make_db()
    air = db.get("Air")
    sio2 = db.get("SiO2")
    tio2 = db.get("TiO2")
    ag = db.get("Ag")
    bk7 = db.get("Glass_BK7")

    scenarios = [
        # (layers, substrate_coherent, angle, pol)
        ([], True, 0.0, "s"),
        ([Layer(sio2, 100.0)], True, 0.0, "s"),
        ([Layer(tio2, 80.0), Layer(sio2, 120.0)], True, 30.0, "p"),
        ([Layer(ag, 50.0)], True, 0.0, "s"),
        ([Layer(sio2, 100.0)], False, 0.0, "s"),
    ]

    for layers, coherent, angle, pol in scenarios:
        st = Structure(layers=layers, incident=air, substrate=bk7,
                       substrate_coherent=coherent)
        res = TMMEngine(st).calculate(WLS, angle=angle, polarization=pol)
        total = res.R + res.T + res.A
        max_dev = np.abs(total - 1.0).max()
        assert max_dev < 1e-6, (
            f"Energy conservation violated: max |R+T+A-1|={max_dev:.2e} "
            f"(layers={len(layers)}, coherent={coherent}, θ={angle}, pol={pol})"
        )
