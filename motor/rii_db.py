"""
Stratoptic — RefractiveIndex.Info Database Parser
===================================================
Parses the open-source refractiveindex.info database (CC0 license).
Source: https://github.com/polyanskiy/refractiveindex.info-database

Author: Necmeddin
"""

import os
import yaml
import numpy as np
from scipy.interpolate import interp1d
from typing import Optional, Tuple


# =============================================================================
# DISPERSION FORMULAS
# =============================================================================

def _apply_formula(formula_type: str, coeffs: np.ndarray,
                   wl_um: np.ndarray) -> np.ndarray:
    """
    Compute n(λ) from dispersion formula coefficients.
    λ in micrometers.
    """
    c = coeffs
    x = wl_um

    if formula_type in ("formula 1", "1"):
        n2 = 1 + c[0]
        for i in range(1, len(c) - 1, 2):
            n2 = n2 + c[i] * x**2 / (x**2 - c[i+1]**2)
        return np.sqrt(np.abs(n2))

    elif formula_type in ("formula 2", "2"):
        n2 = 1 + c[0]
        for i in range(1, len(c) - 1, 2):
            n2 = n2 + c[i] * x**2 / (x**2 - c[i+1])
        return np.sqrt(np.abs(n2))

    elif formula_type in ("formula 3", "3"):
        n2 = c[0]
        for i in range(1, len(c) - 1, 2):
            n2 = n2 + c[i] * x**float(c[i+1])
        return np.sqrt(np.abs(n2))

    elif formula_type in ("formula 4", "4"):
        n2 = (c[0] +
              c[1] * x**c[2] / (x**2 - c[3]**c[4]) +
              c[5] * x**c[6] / (x**2 - c[7]**c[8]))
        for i in range(9, len(c) - 1, 2):
            n2 = n2 + c[i] * x**c[i+1]
        return np.sqrt(np.abs(n2))

    elif formula_type in ("formula 5", "5"):
        n = c[0]
        for i in range(1, len(c) - 1, 2):
            n = n + c[i] * x**float(c[i+1])
        return n

    elif formula_type in ("formula 6", "6"):
        n = 1 + c[0]
        for i in range(1, len(c) - 1, 2):
            n = n + c[i] / (c[i+1] - x**(-2))
        return n

    elif formula_type in ("formula 7", "7"):
        L = 1.0 / (x**2 - 0.028)
        n = c[0] + c[1]*L + c[2]*L**2
        for i, p in enumerate([2, 4, 6]):
            if i + 3 < len(c):
                n = n + c[i+3] * x**p
        return n

    elif formula_type in ("formula 8", "8"):
        r = c[0] + c[1]*x**2/(x**2-c[2]) + c[3]*x**2
        n2 = (1 + 2*r) / (1 - r)
        return np.sqrt(np.abs(n2))

    elif formula_type in ("formula 9", "9"):
        n2 = (c[0] + c[1]/(x**2 - c[2]) +
              c[3]*(x - c[4]) / ((x - c[4])**2 + c[5]))
        return np.sqrt(np.abs(n2))

    else:
        raise ValueError(f"Unknown formula type: {formula_type}")


# =============================================================================
# MATERIAL
# =============================================================================

class RIIMaterial:
    """
    A single optical material from the RII database.
    Provides N(λ) = n(λ) + i·k(λ).
    """

    def __init__(self, name: str, shelf: str, book: str, page: str,
                 yml_path: str):
        self.name     = name
        self.shelf    = shelf
        self.book     = book
        self.page     = page
        self.yml_path = yml_path

        self._interp_n = None
        self._interp_k = None
        self._formula  = None
        self._wl_range = (100.0, 10000.0)  # nm
        self._loaded   = False

    def _load(self):
        if self._loaded:
            return
        self._loaded = True

        with open(self.yml_path, "r", encoding="utf-8") as f:
            parsed = yaml.safe_load(f)

        if not parsed or "DATA" not in parsed:
            return

        for item in parsed["DATA"]:
            t = item.get("type", "").strip()

            # ── Tabulated nk ──────────────────────────────────────────
            if t == "tabulated nk":
                rows = []
                for line in item["data"].strip().split("\n"):
                    vals = line.split()
                    if len(vals) >= 3:
                        rows.append([float(v) for v in vals[:3]])
                if not rows:
                    continue
                arr = np.array(rows)
                wls = arr[:, 0]   # µm
                ns  = arr[:, 1]
                ks  = arr[:, 2]
                self._wl_range = (wls[0] * 1000, wls[-1] * 1000)  # → nm
                kind = "cubic" if len(wls) >= 4 else "linear"
                self._interp_n = interp1d(wls, ns, kind=kind,
                                           fill_value="extrapolate")
                self._interp_k = interp1d(wls, ks, kind=kind,
                                           fill_value="extrapolate")
                return

            # ── Tabulated n ───────────────────────────────────────────
            elif t == "tabulated n":
                rows = []
                for line in item["data"].strip().split("\n"):
                    vals = line.split()
                    if len(vals) >= 2:
                        rows.append([float(v) for v in vals[:2]])
                if not rows:
                    continue
                arr = np.array(rows)
                wls = arr[:, 0]
                ns  = arr[:, 1]
                self._wl_range = (wls[0] * 1000, wls[-1] * 1000)
                kind = "cubic" if len(wls) >= 4 else "linear"
                self._interp_n = interp1d(wls, ns, kind=kind,
                                           fill_value="extrapolate")
                self._interp_k = None
                return

            # ── Formula ───────────────────────────────────────────────
            elif t.startswith("formula"):
                coeffs_raw = item.get("coefficients", "")
                if not coeffs_raw:
                    continue
                coeffs = np.array([float(v) for v in str(coeffs_raw).split()])
                wr = item.get("wavelength_range", "")
                if wr:
                    wr_vals = [float(v) for v in str(wr).split()]
                    self._wl_range = (wr_vals[0] * 1000, wr_vals[1] * 1000)
                self._formula = (t, coeffs)
                return

    def N_at(self, wavelength_nm: float) -> complex:
        """Complex refractive index N = n + ik at wavelength [nm]."""
        self._load()
        wl_um = wavelength_nm / 1000.0

        if self._formula is not None:
            ftype, coeffs = self._formula
            n = float(_apply_formula(ftype, coeffs, np.array([wl_um]))[0])
            return complex(n, 0.0)

        if self._interp_n is not None:
            n = float(self._interp_n(wl_um))
            k = float(self._interp_k(wl_um)) if self._interp_k else 0.0
            return complex(n, k)

        return complex(1.5, 0.0)  # fallback

    @property
    def wl_range_nm(self) -> Tuple[float, float]:
        self._load()
        return self._wl_range

    @property
    def n_ref(self) -> float:
        return self.N_at(550.0).real

    @property
    def k_ref(self) -> float:
        return self.N_at(550.0).imag

    def __repr__(self) -> str:
        return (f"RIIMaterial('{self.name}' | {self.shelf}/{self.book}/{self.page} "
                f"| n@550={self.n_ref:.4f}, k@550={self.k_ref:.4f} "
                f"| λ={self._wl_range[0]:.0f}-{self._wl_range[1]:.0f}nm)")


# =============================================================================
# DATABASE
# =============================================================================

class RIIDatabase:
    """
    Indexes and provides access to the full refractiveindex.info database.

    Usage
    -----
    db = RIIDatabase("~/stratoptic/data/rii_db")
    ag     = db.get("Ag")
    ag_jc  = db.get("Ag", page="Johnson")
    sio2   = db.get("SiO2", page="Malitson")
    """

    def __init__(self, db_root: str):
        self.db_root = os.path.expanduser(db_root)
        self._index: dict[str, list[RIIMaterial]] = {}
        self._build_index()

    def _build_index(self):
        data_root = os.path.join(self.db_root, "database", "data")
        if not os.path.exists(data_root):
            raise FileNotFoundError(f"Database not found: {data_root}")

        count = 0

        def _index_book(shelf, book, book_path):
            nonlocal count
            search_dirs = []
            for sub in ("nk", "n", ""):
                sp = os.path.join(book_path, sub) if sub else book_path
                if os.path.isdir(sp):
                    search_dirs.append(sp)
            found = False
            for sp in search_dirs:
                for fname in sorted(os.listdir(sp)):
                    if not fname.endswith(".yml") or fname == "about.yml":
                        continue
                    found = True
                    page = fname[:-4]
                    yml  = os.path.join(sp, fname)
                    mat  = RIIMaterial(
                        name=book, shelf=shelf, book=book,
                        page=page, yml_path=yml,
                    )
                    self._index.setdefault(book.lower(), []).append(mat)
                    count += 1
            return found

        for shelf in sorted(os.listdir(data_root)):
            shelf_path = os.path.join(data_root, shelf)
            if not os.path.isdir(shelf_path):
                continue
            for lvl1 in sorted(os.listdir(shelf_path)):
                lvl1_path = os.path.join(shelf_path, lvl1)
                if not os.path.isdir(lvl1_path):
                    continue
                if not _index_book(shelf, lvl1, lvl1_path):
                    # Category subfolder (e.g. glass/optical/) — go deeper
                    for lvl2 in sorted(os.listdir(lvl1_path)):
                        lvl2_path = os.path.join(lvl1_path, lvl2)
                        if os.path.isdir(lvl2_path):
                            _index_book(shelf, lvl2, lvl2_path)

        print(f"  RIIDatabase: {len(self._index)} materials, "
              f"{count} datasets indexed.")

    _BUILTINS_FIXED = {
        "Air":    (1.00000, 0.0),
        "Vacuum": (1.00000, 0.0),
    }

    # Sellmeier: [(B1,C1), (B2,C2), (B3,C3)]  — λ in µm
    # n²(λ) = 1 + Σ Bi·λ²/(λ²−Ci)
    _BUILTINS_SELLMEIER = {
        # Schott datasheet
        "Glass_BK7":  [(1.03961212, 0.00600069867),
                       (0.23179234, 0.02001791440),
                       (1.01046945, 103.5606530  )],
        # Malitson (1965)
        "SiO2":       [(0.69616630, 0.00467914826),
                       (0.40794260, 0.01351206300),
                       (0.89747940, 97.9340025   )],
        # Li (1980)
        "MgF2":       [(0.48755108, 0.001882178),
                       (0.39875031, 0.008951478),
                       (2.31203530, 566.135591  )],
        # Dodge (1984)
        "Al2O3":      [(1.43134930, 0.00527992),
                       (0.65054713, 0.01424097),
                       (5.34140210, 325.01783  )],
        # Klocek (1991)
        "CaF2":       [(0.56757760, 0.00252643),
                       (0.47109140, 0.01007833),
                       (3.84845230, 1200.5560  )],
        # Amotchkina (2020)
        "TiO2":       [(5.91370, 0.06916),
                       (0.00000, 0.00000),
                       (0.00000, 0.00000)],
    }

    def _make_fixed(self, name: str, n: float, k: float) -> "RIIMaterial":
        mat = RIIMaterial(name, "builtin", name, "fixed", "")
        mat._loaded = True
        _n, _k = n, k
        mat.N_at = lambda wl, _n=_n, _k=_k: complex(_n, _k)
        mat._wl_range = (100.0, 100000.0)
        return mat

    def _make_sellmeier(self, name: str, coeffs: list) -> "RIIMaterial":
        import numpy as np
        mat = RIIMaterial(name, "builtin", name, "Sellmeier", "")
        mat._loaded = True
        def _n_at(wl_nm, coeffs=coeffs):
            x = wl_nm / 1000.0  # nm → µm
            n2 = 1.0
            for B, C in coeffs:
                if B > 0:
                    n2 += B * x**2 / (x**2 - C)
            return complex(float(np.sqrt(max(n2, 1.0))), 0.0)
        mat.N_at = _n_at
        mat._wl_range = (200.0, 5000.0)
        return mat

    def get(self, name: str,
            page: Optional[str] = None,
            prefer: str = "Johnson") -> RIIMaterial:
        """
        Retrieve a material by name.

        Parameters
        ----------
        name   : e.g. "Ag", "SiO2", "TiO2", "Air", "Glass_BK7"
        page   : specific dataset (e.g. "Johnson", "Malitson")
        prefer : preferred page keyword when multiple exist
        """
        # Fixed built-ins (Air, Vacuum)
        if name in self._BUILTINS_FIXED:
            n, k = self._BUILTINS_FIXED[name]
            return self._make_fixed(name, n, k)

        # Sellmeier built-ins (BK7, SiO2, TiO2...)
        if name in self._BUILTINS_SELLMEIER:
            return self._make_sellmeier(name, self._BUILTINS_SELLMEIER[name])

        # Aliases → Sellmeier built-ins
        aliases = {
            "Glass_BK7":  "Glass_BK7",
            "Quartz":     "SiO2",
        }
        if name in aliases:
            return self._make_sellmeier(
                name, self._BUILTINS_SELLMEIER[aliases[name]]
            )

        key = name.lower()
        if key not in self._index:
            matches = [k for k in self._index if name.lower() in k]
            if not matches:
                raise KeyError(
                    f"Material '{name}' not found.\n"
                    f"Suggestions: {self.search(name, max_results=5)}"
                )
            key = sorted(matches, key=len)[0]

        candidates = self._index[key]

        if page:
            for mat in candidates:
                if page.lower() in mat.page.lower():
                    return mat

        for mat in candidates:
            if prefer.lower() in mat.page.lower():
                return mat

        return candidates[0]

    def search(self, query: str, max_results: int = 10) -> list:
        """Search materials by name."""
        q = query.lower()
        results = []
        for key, mats in self._index.items():
            if q in key:
                results.append(mats[0])
            if len(results) >= max_results:
                break
        return sorted(results, key=lambda m: m.name)

    def list_pages(self, name: str) -> list:
        """List all available dataset pages for a material."""
        key = name.lower()
        if key not in self._index:
            return []
        return [(m.page, m.yml_path) for m in self._index[key]]

    def __len__(self):
        return sum(len(v) for v in self._index.values())

    def __repr__(self):
        return (f"RIIDatabase('{self.db_root}' | "
                f"{len(self._index)} materials, {len(self)} datasets)")
