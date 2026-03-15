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

        R = np.zeros(len(wavelengths))
        T = np.zeros(len(wavelengths))

        for i, wl in enumerate(wavelengths):
            R[i], T[i] = self._calc_single(
                float(wl), angle, polarization,
                substrate_thickness_mm
            )

        A = np.clip(1.0 - R - T, 0.0, 1.0)
        return TMMResult(wavelengths, R, T, A, polarization, angle)

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
