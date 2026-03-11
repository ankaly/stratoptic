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

Sign Convention
---------------
Time dependence: e^(-iωt)  [Born & Wolf]
Phase factor   : δ = (2π/λ) * N * cos(θ) * d
"""

import numpy as np
from dataclasses import dataclass, field


# =============================================================================
# MATERIAL
# =============================================================================

@dataclass
class Material:
    """
    Optical material defined by complex refractive index N = n + ik.

    Parameters
    ----------
    name : str   — material identifier (e.g. 'SiO2', 'TiO2', 'Air')
    n    : float — real part of refractive index
    k    : float — imaginary part / extinction coefficient (default 0)
    """
    name : str
    n    : float
    k    : float = 0.0

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
    material  : Material — optical material of this layer
    thickness : float    — physical thickness [nm]
    """
    material  : Material
    thickness : float  # nm

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
    layers    : list[Layer] — ordered thin film layers (top to bottom)
    incident  : Material   — medium where light originates (default: Air)
    substrate : Material   — semi-infinite substrate (default: Glass n=1.52)
    """
    layers    : list
    incident  : Material = field(default_factory=lambda: Material("Air",   1.0,  0.0))
    substrate : Material = field(default_factory=lambda: Material("Glass", 1.52, 0.0))

    def __repr__(self) -> str:
        stack = " / ".join(
            [self.incident.name] +
            [f"{l.material.name}({l.thickness}nm)" for l in self.layers] +
            [self.substrate.name]
        )
        return f"Structure({stack})"


# =============================================================================
# POLARIZATION
# =============================================================================

class Polarization:
    S        = "s"        # TE — transverse electric
    P        = "p"        # TM — transverse magnetic
    ELLIPTIC = "elliptic" # Incoherent superposition of s and p


# =============================================================================
# RESULT
# =============================================================================

@dataclass
class TMMResult:
    """
    Output of a TMM calculation.

    Attributes
    ----------
    wavelengths  : np.ndarray — wavelength array [nm]
    R            : np.ndarray — reflectance  [0, 1]
    T            : np.ndarray — transmittance [0, 1]
    A            : np.ndarray — absorbance   [0, 1]
    polarization : str
    angle        : float      — angle of incidence [degrees]
    """
    wavelengths  : np.ndarray
    R            : np.ndarray
    T            : np.ndarray
    A            : np.ndarray
    polarization : str
    angle        : float

    def __post_init__(self):
        residual = np.max(np.abs(self.R + self.T + self.A - 1.0))
        assert residual < 1e-10, (
            f"Energy conservation violated: max residual = {residual:.2e}"
        )

    def summary(self) -> str:
        return (
            f"TMMResult | pol={self.polarization} | angle={self.angle}°\n"
            f"  λ range : {self.wavelengths[0]:.1f} – {self.wavelengths[-1]:.1f} nm\n"
            f"  R avg   : {self.R.mean():.4f}\n"
            f"  T avg   : {self.T.mean():.4f}\n"
            f"  A avg   : {self.A.mean():.4f}"
        )


# =============================================================================
# TMM ENGINE
# =============================================================================

class TMMEngine:
    """
    Transfer Matrix Method engine.

    Calculates R, T, A spectra for a multilayer thin film structure
    following the formalism of Born & Wolf (1999), Chapter 1.

    Usage
    -----
    engine = TMMEngine(structure)
    result = engine.calculate(
        wavelengths  = np.linspace(400, 800, 400),
        angle        = 0.0,
        polarization = Polarization.S
    )
    """

    def __init__(self, structure: Structure):
        self.structure = structure

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(
        self,
        wavelengths  : np.ndarray,
        angle        : float = 0.0,
        polarization : str   = Polarization.S
    ) -> TMMResult:
        """
        Run TMM over a wavelength array.

        Parameters
        ----------
        wavelengths  : wavelength array [nm]
        angle        : angle of incidence [degrees], default 0 (normal incidence)
        polarization : Polarization.S | Polarization.P | Polarization.ELLIPTIC
        """
        if polarization == Polarization.ELLIPTIC:
            return self._calculate_elliptic(wavelengths, angle)

        R = np.zeros(len(wavelengths))
        T = np.zeros(len(wavelengths))

        for i, wl in enumerate(wavelengths):
            R[i], T[i] = self._calculate_single(wl, angle, polarization)

        A = 1.0 - R - T
        return TMMResult(
            wavelengths  = wavelengths,
            R=R, T=T, A=A,
            polarization = polarization,
            angle        = angle
        )

    # ------------------------------------------------------------------
    # Core: single wavelength
    # ------------------------------------------------------------------

    def _calculate_single(
        self,
        wavelength   : float,
        angle        : float,
        polarization : str
    ) -> tuple:
        """
        TMM for a single wavelength.

        Returns
        -------
        (R, T) : float, float
        """
        structure = self.structure
        N_inc     = structure.incident.N
        N_sub     = structure.substrate.N
        angle_rad = np.deg2rad(angle)

        # Parallel component of wavevector — conserved via Snell's law
        sin_inc = N_inc * np.sin(angle_rad)

        def cos_theta(N: complex) -> complex:
            """
            cos(θ) in medium N via Snell's law.

            From Snell: N_inc·sin(θ_inc) = N·sin(θ)
            → sin(θ) = sin_inc / N
            → cos(θ) = sqrt(1 - sin²(θ)) = sqrt(1 - (sin_inc/N)²)

            Branch cut: Im(cos_theta) >= 0 so evanescent waves decay.
            """
            sin_sq = (sin_inc / N) ** 2
            ct = np.sqrt(complex(1.0 - sin_sq))
            if ct.imag < 0:
                ct = -ct
            return ct

        cos_inc = cos_theta(N_inc)
        cos_sub = cos_theta(N_sub)

        # Admittance η
        # s (TE): η = N·cos(θ)
        # p (TM): η = N / cos(θ)
        def eta(N: complex, ct: complex) -> complex:
            if polarization == Polarization.S:
                return N * ct
            else:
                return N / ct

        eta_inc = eta(N_inc, cos_inc)
        eta_sub = eta(N_sub, cos_sub)

        # Total transfer matrix M = M_1 @ M_2 @ ... @ M_N
        M = np.eye(2, dtype=complex)

        for layer in structure.layers:
            N_l  = layer.material.N
            ct_l = cos_theta(N_l)
            M_l  = self._build_transfer_matrix(
                N            = N_l,
                cos_theta    = ct_l,
                thickness    = layer.thickness,
                wavelength   = wavelength,
                polarization = polarization
            )
            M = M @ M_l

        # Extract amplitude coefficients from total matrix
        # Born & Wolf §1.6, eq. (1.6.53–54):
        #
        #   r = [(m11 + m12·η_sub)·η_inc − (m21 + m22·η_sub)]
        #       ────────────────────────────────────────────────
        #       [(m11 + m12·η_sub)·η_inc + (m21 + m22·η_sub)]
        #
        #   t = 2·η_inc / denominator

        m11, m12 = M[0, 0], M[0, 1]
        m21, m22 = M[1, 0], M[1, 1]

        A_coeff = (m11 + m12 * eta_sub) * eta_inc
        B_coeff = (m21 + m22 * eta_sub)
        denom   = A_coeff + B_coeff

        r = (A_coeff - B_coeff) / denom
        t = (2.0 * eta_inc) / denom

        # Power reflectance & transmittance
        R = float(np.abs(r) ** 2)
        T = float(np.real(eta_sub) / np.real(eta_inc) * np.abs(t) ** 2)

        # Clamp to [0, 1] — absorb floating point noise
        R = float(np.clip(R, 0.0, 1.0))
        T = float(np.clip(T, 0.0, 1.0))

        return R, T

    # ------------------------------------------------------------------
    # Transfer matrix for a single layer
    # ------------------------------------------------------------------

    def _build_transfer_matrix(
        self,
        N            : complex,
        cos_theta    : complex,
        thickness    : float,
        wavelength   : float,
        polarization : str
    ) -> np.ndarray:
        """
        2×2 characteristic matrix for a single layer.

        Born & Wolf (1999) §1.6, eq. (1.6.51):

            M = [  cos(δ)          −i·sin(δ)/η  ]
                [ −i·η·sin(δ)       cos(δ)      ]

        where:
            δ = (2π/λ) · N · cos(θ) · d   [phase thickness]
            η = N·cos(θ)   for s (TE)
            η = N/cos(θ)   for p (TM)

        Parameters
        ----------
        N            : complex refractive index
        cos_theta    : complex cosine of refraction angle
        thickness    : layer thickness [nm]
        wavelength   : free-space wavelength [nm]
        polarization : 's' or 'p'

        Returns
        -------
        M : np.ndarray shape (2, 2), complex
        """
        # Phase thickness
        delta = (2.0 * np.pi / wavelength) * N * cos_theta * thickness

        # Admittance
        if polarization == Polarization.S:
            eta_l = N * cos_theta
        else:
            eta_l = N / cos_theta

        cos_d = np.cos(delta)
        sin_d = np.sin(delta)

        M = np.array([
            [cos_d,               -1j * sin_d / eta_l],
            [-1j * eta_l * sin_d,  cos_d             ]
        ], dtype=complex)

        return M

    # ------------------------------------------------------------------
    # Elliptic polarization
    # ------------------------------------------------------------------

    def _calculate_elliptic(
        self,
        wavelengths : np.ndarray,
        angle       : float
    ) -> TMMResult:
        """
        Elliptic: incoherent average of s and p results.
        R = 0.5·(R_s + R_p),  T = 0.5·(T_s + T_p)
        """
        res_s = self.calculate(wavelengths, angle, Polarization.S)
        res_p = self.calculate(wavelengths, angle, Polarization.P)

        R = 0.5 * (res_s.R + res_p.R)
        T = 0.5 * (res_s.T + res_p.T)
        A = 1.0 - R - T

        return TMMResult(
            wavelengths  = wavelengths,
            R=R, T=T, A=A,
            polarization = Polarization.ELLIPTIC,
            angle        = angle
        )
    