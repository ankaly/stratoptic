"""
TMM Engine tests — energy conservation, physical laws, edge cases.
"""

import numpy as np
import pytest
import tmm

from motor.engine import TMMEngine, Structure, Layer

WLS = np.linspace(400, 800, 40)  # nm, coarser for speed


def test_default_substrate_is_incoherent(air, glass_bk7):
    """Structure()'s default (substrate_coherent=False, matching
    Sidebar.build_structure()'s default 'Thick substrate' checkbox=on) must
    include back-surface reflection (~8% for bare BK7), not the single-
    interface ~4% a fully coherent calc would give — and must not show
    coherent interference fringes vs wavelength for a thick substrate."""
    st = Structure(layers=[], incident=air, substrate=glass_bk7)  # default
    assert st.substrate_coherent is False
    res = TMMEngine(st).calculate(WLS, polarization="unpolarized")
    assert np.allclose(res.R, 0.081, atol=0.01), (
        f"Bare glass R should be ~8% (front+back), got mean={res.R.mean():.4f}")
    assert res.R.std() < 0.002, (
        "Incoherent substrate R should be flat vs wavelength, not fringing "
        f"(std={res.R.std():.4f})")


def test_air_only(air):
    """No film layers, incident=air, substrate=air -> R~0, T~1."""
    st = Structure(layers=[], incident=air, substrate=air,
                   substrate_coherent=True)
    res = TMMEngine(st).calculate(WLS, angle=0.0, polarization="s")
    assert np.allclose(res.R, 0.0, atol=1e-6), "R should be ~0 for air/air"
    assert np.allclose(res.T, 1.0, atol=1e-6), "T should be ~1 for air/air"


def test_single_dielectric(air, sio2, glass_bk7):
    """SiO2 film on BK7 — R+T+A must equal 1."""
    st = Structure(layers=[Layer(sio2, 100.0)], incident=air, substrate=glass_bk7,
                   substrate_coherent=True)
    res = TMMEngine(st).calculate(WLS, polarization="s")
    total = res.R + res.T + res.A
    assert np.allclose(total, 1.0, atol=1e-6), f"R+T+A not 1: max dev={np.abs(total-1).max()}"


def test_metal_film(air, ag, glass_bk7):
    """50 nm Ag film -> high reflectance (>50%) across visible."""
    st = Structure(layers=[Layer(ag, 50.0)], incident=air, substrate=glass_bk7,
                   substrate_coherent=True)
    res = TMMEngine(st).calculate(WLS, polarization="s")
    assert res.R.mean() > 0.5, f"Ag R mean={res.R.mean():.3f}, expected >0.5"


def test_unpolarized(air, sio2, glass_bk7):
    """Unpolarized result should equal average of s and p."""
    st = Structure(layers=[Layer(sio2, 200.0)], incident=air, substrate=glass_bk7,
                   substrate_coherent=True)
    eng = TMMEngine(st)
    angle = 30.0
    res_s = eng.calculate(WLS, angle=angle, polarization="s")
    res_p = eng.calculate(WLS, angle=angle, polarization="p")
    res_u = eng.calculate(WLS, angle=angle, polarization="unpolarized")
    expected_R = (res_s.R + res_p.R) / 2.0
    assert np.allclose(res_u.R, expected_R, atol=1e-9), "Unpolarized R != (R_s+R_p)/2"


def test_angle_dependence(air, glass_bk7):
    """Reflectance at 45 deg should differ from normal incidence."""
    st = Structure(layers=[], incident=air, substrate=glass_bk7,
                   substrate_coherent=True)
    eng = TMMEngine(st)
    res0 = eng.calculate(WLS, angle=0.0, polarization="s")
    res45 = eng.calculate(WLS, angle=45.0, polarization="s")
    assert not np.allclose(res0.R, res45.R, atol=1e-3), \
        "R at 0 deg and 45 deg should differ"


def test_energy_conservation(air, sio2, tio2, ag, glass_bk7):
    """R + T + A = 1 for every wavelength and scenario."""
    scenarios = [
        # (layers, substrate_coherent, angle, pol)
        ([], True, 0.0, "s"),
        ([Layer(sio2, 100.0)], True, 0.0, "s"),
        ([Layer(tio2, 80.0), Layer(sio2, 120.0)], True, 30.0, "p"),
        ([Layer(ag, 50.0)], True, 0.0, "s"),
        ([Layer(sio2, 100.0)], False, 0.0, "s"),
    ]

    for layers, coherent, angle, pol in scenarios:
        st = Structure(layers=layers, incident=air, substrate=glass_bk7,
                       substrate_coherent=coherent)
        res = TMMEngine(st).calculate(WLS, angle=angle, polarization=pol)
        total = res.R + res.T + res.A
        max_dev = np.abs(total - 1.0).max()
        assert max_dev < 1e-6, (
            f"Energy conservation violated: max |R+T+A-1|={max_dev:.2e} "
            f"(layers={len(layers)}, coherent={coherent}, ang={angle}, pol={pol})"
        )


def test_vectorized_matches_byrnes_reference(air, sio2, tio2, ag, glass_bk7):
    """tmm_vectorized() must match Byrnes' per-wavelength coh_tmm exactly
    (rtol=1e-9), including absorbing layers where Snell branch-cut handling
    is easy to get wrong."""
    scenarios = [
        ([], 0.0, "s"),
        ([Layer(sio2, 100.0)], 0.0, "s"),
        ([Layer(tio2, 80.0), Layer(sio2, 120.0)], 30.0, "p"),
        ([Layer(ag, 50.0)], 0.0, "s"),
        ([Layer(ag, 50.0)], 45.0, "p"),
    ]

    for layers, angle, pol in scenarios:
        st = Structure(layers=layers, incident=air, substrate=glass_bk7,
                       substrate_coherent=True)
        res = TMMEngine(st).calculate(WLS, angle=angle, polarization=pol)

        R_ref = np.zeros(len(WLS))
        T_ref = np.zeros(len(WLS))
        for i, wl in enumerate(WLS):
            n_list = ([air.N_at(wl)] + [l.material.N_at(wl) for l in layers]
                      + [glass_bk7.N_at(wl)])
            d_list = [np.inf] + [l.thickness for l in layers] + [np.inf]
            out = tmm.coh_tmm(pol, n_list, d_list, np.deg2rad(angle), float(wl))
            R_ref[i] = out['R']
            T_ref[i] = out['T']

        assert np.allclose(res.R, R_ref, rtol=1e-9, atol=1e-12), (
            f"R mismatch vs Byrnes (layers={len(layers)}, ang={angle}, pol={pol}): "
            f"max diff={np.abs(res.R - R_ref).max():.2e}"
        )
        assert np.allclose(res.T, T_ref, rtol=1e-9, atol=1e-12), (
            f"T mismatch vs Byrnes (layers={len(layers)}, ang={angle}, pol={pol}): "
            f"max diff={np.abs(res.T - T_ref).max():.2e}"
        )
