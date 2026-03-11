"""
Stratoptic - Transfer Matrix Method (TMM) Engine
=================================================
Author      : Necmeddin
Institution : Gazi University, Department of Photonics
Version     : 0.1.0 (Python prototype)
License     : TBD

References
----------
[1] Hecht, E. (2002). Optics (4th ed.). Addison Wesley.
[2] Born, M., & Wolf, E. (1999). Principles of Optics (7th ed.). Cambridge University Press.
[3] Saleh, B. E. A., & Teich, M. C. (2007). Fundamentals of Photonics (2nd ed.). Wiley.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


# =============================================================================
# MATERIAL
# =============================================================================

@dataclass
class Material:
    """
    Optical material defined by complex refractive index N = n + ik.

    Parameters
    ----------
    name : str
        Material identifier (e.g. 'SiO2', 'TiO2', 'Air')
    n : float
        Real part of refractive index (refractive index)
    k : float
        Imaginary part of refractive index (extinction coefficient)
    """
    name: str
    n: float
    k: float = 0.0

    @property
    def N(self) -> complex:
        """Complex refractive index N = n + ik."""
        return complex(self.n, self.k)

    def __repr__(self) -> str:
        return f"Material('{self.name}', n={self.n}, k={self.k})"


# =============================================================================
# LAYER
# =============================================================================

@dataclass
class Layer:
    """
    A single thin film layer.

    Parameters
    ----------
    material : Material
        Optical material of this layer
    thickness : float
        Physical thickness in nanometers [nm]
    """
    material: Material
    thickness: float  # nm

    def __repr__(self) -> str:
        return f"Layer({self.material.name}, d={self.thickness} nm)"


# =============================================================================
# STRUCTURE
# =============================================================================

@dataclass
class Structure:
    """
    Complete thin film stack: incident medium / [layers] / substrate.

    Parameters
    ----------
    layers : list[Layer]
        Ordered list of thin film layers (top to bottom)
    incident : Material
        Medium where light originates (typically Air)
    substrate : Material
        Semi-infinite substrate below the stack (typically Glass)
    """
    layers: list
    incident: Material = field(default_factory=lambda: Material("Air", 1.0, 0.0))
    substrate: Material = field(default_factory=lambda: Material("Glass", 1.52, 0.0))

    def __repr__(self) -> str:
        stack = " / ".join([self.incident.name] +
                           [f"{l.material.name}({l.thickness}nm)" for l in self.layers] +
                           [self.substrate.name])
        return f"Structure({stack})"


# =============================================================================
# POLARIZATION
# =============================================================================

class Polarization:
    """Supported polarization modes."""
    S = "s"          # TE - transverse electric
    P = "p"          # TM - transverse magnetic
    ELLIPTIC = "elliptic"


# =============================================================================
# RESULT
# =============================================================================

@dataclass
class TMMResult:
    """
    Output of a TMM calculation.

    Parameters
    ----------
    wavelengths : np.ndarray
        Wavelength array [nm]
    R : np.ndarray
        Reflectance spectrum [0, 1]
    T : np.ndarray
        Transmittance spectrum [0, 1]
    A : np.ndarray
        Absorbance spectrum [0, 1]  (A = 1 - R - T)
    polarization : str
        Polarization mode used
    angle : float
        Angle of incidence in degrees
    """
    wavelengths: np.ndarray
    R: np.ndarray
    T: np.ndarray
    A: np.ndarray
    polarization: str
    angle: float

    def __post_init__(self):
        # Sanity check: R + T + A = 1 (within numerical tolerance)
        residual = np.max(np.abs(self.R + self.T + self.A - 1.0))
        assert residual < 1e-10, f"Energy conservation violated: max residual = {residual:.2e}"

    def summary(self) -> str:
        return (
            f"TMMResult | pol={self.polarization} | angle={self.angle}°\n"
            f"  λ range : {self.wavelengths[0]:.1f} - {self.wavelengths[-1]:.1f} nm\n"
            f"  R avg  : {self.R.mean():.4f}\n"
            f"  T avg  : {self.T.mean():.4f}\n"
            f"  A avg  : {self.A.mean():.4f}"
        )


# =============================================================================
# TMM ENGINE
# =============================================================================

class TMMEngine:
    """
    Transfer Matrix Method engine.

    Calculates reflectance (R), transmittance (T), and absorbance (A)
    spectra for a multilayer thin film structure.

    Usage
    -----
    engine = TMMEngine(structure)
    result = engine.calculate(
        wavelengths=np.linspace(400, 800, 400),
        angle=0.0,
        polarization=Polarization.S
    )
    """

    def __init__(self, structure: Structure):
        self.structure = structure

    def calculate(
        self,
        wavelengths: np.ndarray,
        angle: float = 0.0,
        polarization: str = Polarization.S
    ) -> TMMResult:
        """
        Run TMM calculation over a wavelength range.

        Parameters
        ----------
        wavelengths : np.ndarray
            Wavelength array in nanometers [nm]
        angle : float
            Angle of incidence in degrees (0 = normal incidence)
        polarization : str
            'S', 'P', or 'elliptic'

        Returns
        -------
        TMMResult
        """
        if polarization == Polarization.ELLIPTIC:
            return self._calculate_elliptic(wavelengths, angle)

        R = np.zeros(len(wavelengths))
        T = np.zeros(len(wavelengths))

        for i, wl in enumerate(wavelengths):
            r, t = self._calculate_single(wl, angle, polarization)
            R[i] = r
            T[i] = t

        A = 1.0 - R - T

        return TMMResult(
            wavelengths=wavelengths,
            R=R, T=T, A=A,
            polarization=polarization,
            angle=angle
        )

    def _calculate_single(
        self,
        wavelength: float,
        angle: float,
        polarization: str
    ) -> tuple:
        """
        TMM calculation for a single wavelength.

        Returns
        -------
        (R, T) : tuple of floats
        """
        # TODO: Implement core TMM algorithm
        # Step 1: Compute k_z for each layer using Snell's law
        # Step 2: Build characteristic matrix M_i for each layer
        # Step 3: Multiply matrices: M = M_1 @ M_2 @ ... @ M_N
        # Step 4: Extract r and t from total matrix
        # Step 5: Compute R = |r|^2, T = (n_sub/n_inc) * |t|^2
        raise NotImplementedError("TMM core not yet implemented.")

    def _calculate_elliptic(
        self,
        wavelengths: np.ndarray,
        angle: float
    ) -> TMMResult:
        """
        Elliptic polarization: incoherent superposition of s and p.
        R = 0.5 * (R_s + R_p), T = 0.5 * (T_s + T_p)
        """
        result_s = self.calculate(wavelengths, angle, Polarization.S)
        result_p = self.calculate(wavelengths, angle, Polarization.P)

        R = 0.5 * (result_s.R + result_p.R)
        T = 0.5 * (result_s.T + result_p.T)
        A = 1.0 - R - T

        return TMMResult(
            wavelengths=wavelengths,
            R=R, T=T, A=A,
            polarization=Polarization.ELLIPTIC,
            angle=angle
        )

    def _build_transfer_matrix(
        self,
        N: complex,
        cos_theta: complex,
        thickness: float,
        wavelength: float,
        polarization: str
    ) -> np.ndarray:
        """
        Build 2x2 characteristic matrix for a single layer.

        Parameters
        ----------
        N         : complex refractive index
        cos_theta : complex cosine of refraction angle (Snell's law)
        thickness : layer thickness [nm]
        wavelength: free-space wavelength [nm]
        polarization: 's' or 'p'

        Returns
        -------
        M : np.ndarray, shape (2, 2), complex
        """
        # TODO: Implement
        # delta = (2 * pi / wavelength) * N * cos_theta * thickness
        # eta = N * cos_theta        (for s polarization)
        # eta = N / cos_theta        (for p polarization)  ← check sign convention
        # M = [[cos(delta),        -1j * sin(delta) / eta],
        #      [-1j * eta * sin(delta),  cos(delta)      ]]
        raise NotImplementedError("Transfer matrix not yet implemented.")