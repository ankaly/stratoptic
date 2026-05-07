"""
RIIDatabase tests — material retrieval, Sellmeier, search, formula types.
"""

import numpy as np


def test_get_air(db):
    """Air: n=1, k=0 at all wavelengths."""
    air = db.get("Air")
    for wl in [400, 550, 800]:
        N = air.N_at(wl)
        assert abs(N.real - 1.0) < 1e-6, f"Air n@{wl}nm = {N.real}, expected 1.0"
        assert abs(N.imag) < 1e-6, f"Air k@{wl}nm = {N.imag}, expected 0.0"


def test_get_ag(db):
    """Silver: complex N, k > 0 in visible range."""
    ag = db.get("Ag")
    N = ag.N_at(550)
    assert isinstance(N, complex), "N_at should return complex"
    assert N.imag > 0, f"Ag k@550nm = {N.imag}, expected > 0"


def test_sellmeier_bk7(glass_bk7):
    """BK7 Sellmeier: n ~ 1.52 at 550 nm."""
    n = glass_bk7.N_at(550).real
    assert abs(n - 1.52) < 0.02, f"BK7 n@550nm = {n:.4f}, expected ~1.52"


def test_search(db):
    """Searching 'ti' should return at least one TiO2-like result."""
    results = db.search("ti")
    names_lower = [m.name.lower() for m in results]
    assert any("ti" in n for n in names_lower), \
        f"Search 'ti' returned no Ti materials: {names_lower}"


def test_formula_types(db):
    """
    At minimum formula types 1 (BK7/SiO2), 2 (Sellmeier variant), and 3
    should each produce physically reasonable n values.
    """
    bk7 = db.get("Glass_BK7")
    n1 = bk7.N_at(550).real
    assert 1.4 < n1 < 1.7, f"Formula-1 (BK7) n@550nm out of range: {n1}"

    sio2 = db.get("SiO2")
    n2 = sio2.N_at(550).real
    assert 1.4 < n2 < 1.6, f"Formula-2 (SiO2) n@550nm out of range: {n2}"

    tio2 = db.get("TiO2")
    n3 = tio2.N_at(550).real
    assert 2.0 < n3 < 3.2, f"TiO2 n@550nm out of range: {n3}"
