"""
Stratoptic — TMM Engine
========================
Byrnes (2021) tmm package + refractiveindex.info database.

Author: Necmeddin
"""

import numpy as np
import tmm
from dataclasses import dataclass
from typing import Optional
from motor.rii_db import RIIDatabase, RIIMaterial


# =============================================================================
# LAYER & STRUCTURE
# =============================================================================

class Layer:
    def __init__(self, material: RIIMaterial, thickness: float,
                 coherent: bool = True):
        self.material  = material
        self.thickness = thickness
        self.coherent  = coherent

    def __repr__(self):
        return f"Layer({self.material.name}, d={self.thickness:.1f}nm)"


class Structure:
    def __init__(self, layers: list,
                 incident:  Optional[RIIMaterial] = None,
                 substrate: Optional[RIIMaterial] = None,
                 substrate_coherent: bool = False):
        """
        Parameters
        ----------
        layers             : list of Layer objects
        incident           : incident medium (default: Air)
        substrate          : substrate (default: Glass_BK7)
        substrate_coherent : False = incoherent 1mm glass (realistic)
                             True  = coherent (for freestanding films)
        """
        self.layers             = layers
        self.substrate_coherent = substrate_coherent

        db = _get_default_db()
        self.incident  = incident  or db.get("Air")
        self.substrate = substrate or db.get("BK7", prefer="Sellmeier")

    def __repr__(self):
        stack = " / ".join(
            [self.incident.name] +
            [f"{l.material.name}({l.thickness:.0f}nm)" for l in self.layers] +
            [self.substrate.name]
        )
        return f"Structure({stack})"


# =============================================================================
# VECTORIZED COHERENT TMM CORE
# =============================================================================
# Byrnes (tmm package) coh_tmm runs one Python loop iteration per wavelength.
# These helpers replicate its exact algorithm (interface + propagation
# matrices, https://arxiv.org/abs/1603.02720) but broadcast every step over
# the full wavelength axis at once — the remaining Python loop is over layers
# only (typically 5-50), not over wavelengths (typically hundreds-thousands).

def _is_forward_angle_vec(n: np.ndarray, theta: np.ndarray) -> np.ndarray:
    ncostheta = n * np.cos(theta)
    use_imag = np.abs(ncostheta.imag) > 1e-10
    return np.where(use_imag, ncostheta.imag > 0, ncostheta.real > 0)


def _list_snell_vec(n_stack: np.ndarray, theta0: float) -> np.ndarray:
    """Vectorized Snell's law. n_stack: (num_layers, n_wl) complex."""
    angles = np.arcsin(n_stack[0] * np.sin(theta0) / n_stack + 0j)
    fwd0 = _is_forward_angle_vec(n_stack[0], angles[0])
    angles[0] = np.where(fwd0, angles[0], np.pi - angles[0])
    fwdN = _is_forward_angle_vec(n_stack[-1], angles[-1])
    angles[-1] = np.where(fwdN, angles[-1], np.pi - angles[-1])
    return angles


def _fresnel_vec(pol: str, n_i, n_f, th_i, th_f):
    cos_i, cos_f = np.cos(th_i), np.cos(th_f)
    if pol == 's':
        r = (n_i * cos_i - n_f * cos_f) / (n_i * cos_i + n_f * cos_f)
        t = 2 * n_i * cos_i / (n_i * cos_i + n_f * cos_f)
    else:
        r = (n_f * cos_i - n_i * cos_f) / (n_f * cos_i + n_i * cos_f)
        t = 2 * n_i * cos_i / (n_f * cos_i + n_i * cos_f)
    return r, t


def _matmul2x2(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """A, B: (2,2,n_wl) complex — elementwise (over n_wl) 2x2 matrix product."""
    return np.einsum('abk,bck->ack', A, B)


def tmm_vectorized(n_stack: np.ndarray, d_stack: np.ndarray,
                    wl: np.ndarray, theta0: float, pol: str) -> tuple:
    """
    Coherent TMM, vectorized across the wavelength axis.

    n_stack : complex array (n_layers+2, n_wl) — N per layer (incl. incident
              & exit semi-infinite media) at each wavelength
    d_stack : float array (n_layers+2,) — thickness nm; first & last = inf
    wl      : float array (n_wl,) — vacuum wavelength, nm
    theta0  : angle of incidence, radians
    pol     : 's' or 'p'

    Returns (R, T) — float arrays (n_wl,).
    """
    num_layers, n_wl = n_stack.shape
    th = _list_snell_vec(n_stack, theta0)
    kz = 2 * np.pi * n_stack * np.cos(th) / wl[None, :]

    with np.errstate(invalid='ignore'):
        delta = kz * d_stack[:, None]
    delta = np.where(delta.imag > 35, delta.real + 35j, delta)

    ones = np.ones(n_wl, dtype=complex)
    zeros = np.zeros(n_wl, dtype=complex)

    r01, t01 = _fresnel_vec(pol, n_stack[0], n_stack[1], th[0], th[1])
    M = np.array([[ones, r01], [r01, ones]]) / t01

    for i in range(1, num_layers - 1):
        r_i, t_i = _fresnel_vec(pol, n_stack[i], n_stack[i + 1], th[i], th[i + 1])
        L = np.array([[np.exp(-1j * delta[i]), zeros],
                      [zeros, np.exp(1j * delta[i])]])
        I = np.array([[ones, r_i], [r_i, ones]]) / t_i
        M = _matmul2x2(M, _matmul2x2(L, I))

    r = M[1, 0] / M[0, 0]
    t = 1.0 / M[0, 0]

    R = np.abs(r) ** 2
    if pol == 's':
        T = (np.abs(t) ** 2 * (n_stack[-1] * np.cos(th[-1])).real
             / (n_stack[0] * np.cos(th[0])).real)
    else:
        T = (np.abs(t) ** 2 * (n_stack[-1] * np.conj(np.cos(th[-1]))).real
             / (n_stack[0] * np.conj(np.cos(th[0]))).real)

    return np.clip(R, 0.0, 1.0), np.clip(T, 0.0, 1.0)


# =============================================================================
# RESULT
# =============================================================================

@dataclass
class TMMResult:
    wavelengths  : np.ndarray
    R            : np.ndarray
    T            : np.ndarray
    A            : np.ndarray
    polarization : str
    angle        : float

    def summary(self) -> str:
        return (
            f"TMMResult | pol={self.polarization} | angle={self.angle}°\n"
            f"  λ: {self.wavelengths[0]:.0f}–{self.wavelengths[-1]:.0f} nm\n"
            f"  R avg={self.R.mean()*100:.2f}%  "
            f"T avg={self.T.mean()*100:.2f}%  "
            f"A avg={self.A.mean()*100:.2f}%"
        )


# =============================================================================
# ENGINE
# =============================================================================

class TMMEngine:
    """
    Thin film calculation engine.

    Coherent layers  → Byrnes coh_tmm (exact interference)
    Incoherent substrate → Byrnes inc_tmm (real glass substrates)
    """

    def __init__(self, structure: Structure):
        self.st = structure

    def calculate(self,
                  wavelengths: np.ndarray,
                  angle: float = 0.0,
                  polarization: str = "s",
                  substrate_thickness_mm: float = 1.0) -> TMMResult:
        """
        Parameters
        ----------
        wavelengths            : nm array
        angle                  : degrees
        polarization           : 's', 'p', or 'unpolarized'
        substrate_thickness_mm : substrate thickness in mm (default 1mm)
        """
        if polarization == "unpolarized":
            return self._unpolarized(wavelengths, angle, substrate_thickness_mm)

        if self.st.substrate_coherent:
            R, T = self._calc_coherent_vectorized(wavelengths, angle, polarization)
        else:
            R = np.zeros(len(wavelengths))
            T = np.zeros(len(wavelengths))
            for i, wl in enumerate(wavelengths):
                R[i], T[i] = self._calc_single(
                    float(wl), angle, polarization,
                    substrate_thickness_mm
                )

        A = np.clip(1.0 - R - T, 0.0, 1.0)
        return TMMResult(wavelengths, R, T, A, polarization, angle)

    def _calc_coherent_vectorized(self, wavelengths: np.ndarray, angle: float,
                                  pol: str) -> tuple:
        st = self.st
        wl = np.asarray(wavelengths, dtype=float)

        n_stack = np.stack(
            [st.incident.N_array(wl)] +
            [l.material.N_array(wl) for l in st.layers] +
            [st.substrate.N_array(wl)]
        )
        d_stack = np.array(
            [np.inf] + [l.thickness for l in st.layers] + [np.inf]
        )
        return tmm_vectorized(n_stack, d_stack, wl, np.deg2rad(angle), pol)

    def _calc_single(self, wl_nm: float, angle: float, pol: str,
                     sub_thick_mm: float) -> tuple:
        st = self.st

        if st.substrate_coherent:
            # Fully coherent stack — freestanding film or thin substrate
            n_list = (
                [st.incident.N_at(wl_nm)] +
                [l.material.N_at(wl_nm) for l in st.layers] +
                [st.substrate.N_at(wl_nm)]
            )
            d_list = (
                [np.inf] +
                [l.thickness for l in st.layers] +
                [np.inf]
            )
            res = tmm.coh_tmm(pol, n_list, d_list, np.deg2rad(angle), wl_nm)
            R = tmm.R_from_r(res['r'])
            th_f = tmm.snell(n_list[0], n_list[-1], np.deg2rad(angle))
            T = tmm.T_from_t(pol, res['t'], n_list[0], n_list[-1],
                              np.deg2rad(angle), th_f)
        else:
            # Incoherent substrate — realistic case for glass
            # inc_tmm: pol, n_list, d_list, c_list, th_0, lam_vac
            # c_list: 'c' = coherent, 'i' = incoherent
            # Incident and exit must be 'i' in inc_tmm convention
            sub_nm = sub_thick_mm * 1e6  # mm → nm

            N_inc  = st.incident.N_at(wl_nm)
            N_sub  = st.substrate.N_at(wl_nm)
            N_exit = complex(1.0, 0.0)  # air exit

            n_list = ([N_inc] +
                      [l.material.N_at(wl_nm) for l in st.layers] +
                      [N_sub, N_exit])
            d_list = ([np.inf] +
                      [l.thickness for l in st.layers] +
                      [sub_nm, np.inf])
            # incident='i', coherent films='c', substrate='i', exit='i'
            c_list = (['i'] +
                      ['c'] * len(st.layers) +
                      ['i', 'i'])

            res = tmm.inc_tmm(pol, n_list, d_list, c_list,
                              np.deg2rad(angle), wl_nm)
            R = res['R']
            T = res['T']

        return float(np.clip(R, 0, 1)), float(np.clip(T, 0, 1))

    def electric_field(self, wavelength_nm: float, angle: float = 0.0,
                       polarization: str = "s",
                       points_per_layer: int = 100) -> dict:
        """
        Single-wavelength |E|² distribution across the layer stack.

        Uses coherent TMM only (incident + film stack + substrate, all coherent).
        Incident and exit media are shown over a 50 nm window.

        Returns
        -------
        dict with keys:
            positions_nm     : np.ndarray  — x axis (nm, 0 = first film surface)
            E_squared        : np.ndarray  — |E/E₀|²
            layer_boundaries : list[float] — interface positions (nm)
            layer_names      : list[str]   — name for each region
        """
        st = self.st
        wl = float(wavelength_nm)
        pol = polarization if polarization != "unpolarized" else "s"
        th0 = np.deg2rad(angle)

        SEMI_INF_NM = 50.0   # nm shown for incident and exit media

        # Build coherent n_list / d_list (incident + films + substrate)
        n_list = (
            [st.incident.N_at(wl)] +
            [l.material.N_at(wl) for l in st.layers] +
            [st.substrate.N_at(wl)]
        )
        d_list = (
            [np.inf] +
            [l.thickness for l in st.layers] +
            [np.inf]
        )

        coh_data = tmm.coh_tmm(pol, n_list, d_list, th0, wl)

        # Layer names for regions
        layer_names = (
            [st.incident.name] +
            [f"{l.material.name} ({l.thickness:.0f} nm)" for l in st.layers] +
            [st.substrate.name]
        )

        # Sample positions and compute |E|²
        positions = []
        E_sq = []

        # Layer 0: incident medium, show last SEMI_INF_NM nm before interface
        pts0 = np.linspace(-SEMI_INF_NM, 0.0, points_per_layer, endpoint=False)
        for d in pts0:
            pr = tmm.position_resolved(0, d, coh_data)
            positions.append(d)
            E_sq.append(abs(pr['Ex'])**2 + abs(pr['Ey'])**2 + abs(pr['Ez'])**2)

        # Film layers (1 … N-1, excluding exit)
        offset = 0.0
        boundaries = [0.0]
        for i, layer in enumerate(st.layers):
            thick = layer.thickness
            pts = np.linspace(0.0, thick, points_per_layer, endpoint=False)
            layer_idx = i + 1
            for d in pts:
                pr = tmm.position_resolved(layer_idx, d, coh_data)
                positions.append(offset + d)
                E_sq.append(abs(pr['Ex'])**2 + abs(pr['Ey'])**2 + abs(pr['Ez'])**2)
            offset += thick
            boundaries.append(offset)

        # Last layer: substrate, show first SEMI_INF_NM nm after last interface
        last_idx = len(n_list) - 1
        pts_sub = np.linspace(0.0, SEMI_INF_NM, points_per_layer, endpoint=True)
        for d in pts_sub:
            pr = tmm.position_resolved(last_idx, d, coh_data)
            positions.append(offset + d)
            E_sq.append(abs(pr['Ex'])**2 + abs(pr['Ey'])**2 + abs(pr['Ez'])**2)

        return {
            'positions_nm'     : np.array(positions),
            'E_squared'        : np.array(E_sq),
            'layer_boundaries' : boundaries,
            'layer_names'      : layer_names,
        }

    def _unpolarized(self, wavelengths, angle, sub_thick_mm):
        res_s = self.calculate(wavelengths, angle, 's', sub_thick_mm)
        res_p = self.calculate(wavelengths, angle, 'p', sub_thick_mm)
        R = 0.5 * (res_s.R + res_p.R)
        T = 0.5 * (res_s.T + res_p.T)
        A = np.clip(1.0 - R - T, 0.0, 1.0)
        return TMMResult(wavelengths, R, T, A, "unpolarized", angle)


# =============================================================================
# DEFAULT DATABASE SINGLETON
# =============================================================================

_db_instance: Optional[RIIDatabase] = None

def _get_default_db() -> RIIDatabase:
    global _db_instance
    if _db_instance is None:
        import os
        root = os.path.join(os.path.dirname(__file__),
                            "..", "data", "rii_db")
        _db_instance = RIIDatabase(root)
    return _db_instance

def get_db() -> RIIDatabase:
    return _get_default_db()
