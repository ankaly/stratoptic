import numpy as np
from PyQt6.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches

from ui.theme import DARK


class SpectrumCanvas(FigureCanvas):
    CR = "#FF453A"; CT = "#0A84FF"; CA = "#32D74B"

    def __init__(self, t, parent=None):
        self.t = t
        self.fig = Figure(facecolor=t["plot_bg"])
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._res = self._st = None
        self._sR = self._sT = self._sA = True
        self._overlays = []
        self._empty()

    def apply_theme(self, t):
        self.t = t; self.fig.set_facecolor(t["plot_bg"])
        if self._res:
            self.plot(self._res, self._sR, self._sT, self._sA, self._st,
                      overlays=self._overlays)
        else:
            self._empty()

    def _style(self, ax):
        ax.tick_params(colors=self.t["t2"], labelsize=9, length=3, width=0.6)
        ax.set_xlabel("Wavelength (nm)", color=self.t["t2"], fontsize=10, labelpad=5)
        ax.set_ylabel("Intensity (%)", color=self.t["t2"], fontsize=10, labelpad=5)
        ax.set_xlim(380, 800); ax.set_ylim(-2, 102)
        ax.grid(True, color=self.t["plot_grid"], lw=0.5, alpha=1.0)
        ax.grid(True, which="minor", color=self.t["plot_grid"], lw=0.3, alpha=0.5)
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        for sp in ax.spines.values():
            sp.set_edgecolor(self.t["plot_grid"]); sp.set_linewidth(0.6)

    def _empty(self):
        self.fig.clear()
        gs = gridspec.GridSpec(1, 1, figure=self.fig,
                               left=0.07, right=0.98, top=0.95, bottom=0.10)
        ax = self.fig.add_subplot(gs[0], facecolor=self.t["plot_ax"])
        self._style(ax)
        ax.text(0.5, 0.5, "Add layers and click  Calculate",
                transform=ax.transAxes, ha="center", va="center",
                color=self.t["t2"], fontsize=13)
        self.draw()

    def _mark_minmax(self, ax, wl, vals, color):
        """Mark max and min points on a curve if values are in range 1–99%."""
        bbox = dict(boxstyle="round,pad=0.2", facecolor=self.t["plot_ax"],
                    edgecolor=color, alpha=0.75, linewidth=0.8)
        for idx, is_max in [(np.argmax(vals), True), (np.argmin(vals), False)]:
            v = vals[idx]
            if not (1.0 < v < 99.0):
                continue
            ax.plot(wl[idx], v, 'o', color=color, markersize=6,
                    markeredgewidth=1.2, markeredgecolor=self.t["plot_bg"],
                    zorder=5)
            offset = (0, 12) if is_max else (0, -16)
            va = "bottom" if is_max else "top"
            ax.annotate(f"{v:.1f}%\n{wl[idx]:.0f}nm",
                        xy=(wl[idx], v), xytext=offset,
                        textcoords="offset points",
                        fontsize=7, color=color, va=va, ha="center",
                        bbox=bbox, zorder=6)

    def _structure_label(self, structure, result):
        pol = result.polarization.upper()
        if structure:
            title = " / ".join(
                [structure.incident.name] +
                [f"{l.material.name}({l.thickness:.0f})" for l in structure.layers] +
                [structure.substrate.name])
            return title + f"  θ={result.angle}°"
        return f"TMM  {pol}  θ={result.angle}°"

    def plot(self, result, sR=True, sT=True, sA=True, structure=None, overlays=None):
        self._res = result; self._st = structure
        self._sR = sR; self._sT = sT; self._sA = sA
        self._overlays = overlays or []
        self.fig.clear(); self.fig.set_facecolor(self.t["plot_bg"])
        gs = gridspec.GridSpec(1, 1, figure=self.fig,
                               left=0.07, right=0.98, top=0.92, bottom=0.10)
        ax = self.fig.add_subplot(gs[0], facecolor=self.t["plot_ax"])
        self._style(ax)

        # Draw overlays first (behind main result)
        for ov_result, ov_structure, ov_color in self._overlays:
            ov_wl = ov_result.wavelengths
            lbl = self._structure_label(ov_structure, ov_result)
            if sR:
                ax.plot(ov_wl, ov_result.R*100, color=ov_color, lw=1.2,
                        alpha=0.4, label=f"R  {lbl}", zorder=2)
            if sT:
                ax.plot(ov_wl, ov_result.T*100, color=ov_color, lw=1.2,
                        alpha=0.4, linestyle="--", label=f"T  {lbl}", zorder=2)
            if sA:
                ax.plot(ov_wl, ov_result.A*100, color=ov_color, lw=1.2,
                        alpha=0.4, linestyle=":", label=f"A  {lbl}", zorder=2)

        # Draw main result on top
        wl = result.wavelengths
        if sR:
            ax.plot(wl, result.R*100, color=self.CR, lw=2.0,
                    label="Reflectance (R)", zorder=3)
            ax.fill_between(wl, result.R*100, alpha=0.07, color=self.CR)
            self._mark_minmax(ax, wl, result.R*100, self.CR)
        if sT:
            ax.plot(wl, result.T*100, color=self.CT, lw=2.0,
                    label="Transmittance (T)", zorder=3)
            ax.fill_between(wl, result.T*100, alpha=0.07, color=self.CT)
            self._mark_minmax(ax, wl, result.T*100, self.CT)
        if sA:
            ax.plot(wl, result.A*100, color=self.CA, lw=2.0,
                    label="Absorbance (A)", zorder=3)
            ax.fill_between(wl, result.A*100, alpha=0.07, color=self.CA)
            self._mark_minmax(ax, wl, result.A*100, self.CA)

        ax.legend(loc="upper right", fontsize=8,
                  facecolor=self.t["plot_ax"], labelcolor=self.t["t1"],
                  edgecolor=self.t["plot_grid"], framealpha=0.95,
                  handlelength=1.5, handletextpad=0.5)
        ax.set_xlim(wl[0], wl[-1]); ax.set_ylim(-2, 102)
        pol = result.polarization.upper()
        if structure:
            title = " / ".join(
                [structure.incident.name] +
                [f"{l.material.name}({l.thickness:.0f})" for l in structure.layers] +
                [structure.substrate.name])
            title += f"   ·   {pol}   ·   θ={result.angle}°"
        else:
            title = f"TMM Spectrum   ·   {pol}   ·   θ={result.angle}°"
        self.fig.suptitle(title, color=self.t["t2"], fontsize=8.5,
                          x=0.5, y=0.99, ha="center")
        self.draw()

    def save(self, path):
        self.fig.savefig(path, dpi=300, bbox_inches="tight",
                         facecolor=self.t["plot_bg"])


class DispersionCanvas(FigureCanvas):
    CN = "#0A84FF"; CK = "#FF453A"

    def __init__(self, t, parent=None):
        self.t = t
        self.fig = Figure(facecolor=t["plot_bg"])
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._empty()

    def apply_theme(self, t):
        self.t = t; self.fig.set_facecolor(t["plot_bg"]); self.draw()

    def _sax(self, ax):
        ax.tick_params(colors=self.t["t2"], labelsize=9, length=3, width=0.6)
        ax.grid(True, color=self.t["plot_grid"], lw=0.5)
        ax.grid(True, which="minor", color=self.t["plot_grid"], lw=0.3, alpha=0.5)
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        for sp in ax.spines.values():
            sp.set_edgecolor(self.t["plot_grid"]); sp.set_linewidth(0.6)

    def _empty(self):
        self.fig.clear(); self.fig.set_facecolor(self.t["plot_bg"])
        ax = self.fig.add_subplot(111, facecolor=self.t["plot_bg"]); ax.axis("off")
        ax.text(0.5, 0.5, "Select a material to view dispersion",
                transform=ax.transAxes, ha="center", va="center",
                color=self.t["t2"], fontsize=11)
        self.draw()

    def plot(self, mat, db):
        self.fig.clear(); self.fig.set_facecolor(self.t["plot_bg"])
        try:
            wl0, wl1 = mat.wl_range_nm
            wl0 = max(wl0, 200); wl1 = min(wl1, 2500)
            if wl1-wl0 < 10: wl0, wl1 = 200, 1800
        except: wl0, wl1 = 200, 1800
        wl = np.linspace(wl0, wl1, 500)
        nv = np.array([mat.N_at(w).real for w in wl])
        kv = np.array([mat.N_at(w).imag for w in wl])
        has_k = kv.max() > 0.001
        m = dict(left=0.09, right=0.97, top=0.90, bottom=0.11)
        if has_k:
            gs = gridspec.GridSpec(2, 1, figure=self.fig, hspace=0.06, **m)
            an = self.fig.add_subplot(gs[0], facecolor=self.t["plot_ax"])
            ak = self.fig.add_subplot(gs[1], facecolor=self.t["plot_ax"], sharex=an)
        else:
            gs = gridspec.GridSpec(1, 1, figure=self.fig, **m)
            an = self.fig.add_subplot(gs[0], facecolor=self.t["plot_ax"]); ak = None
        self._sax(an)
        an.plot(wl, nv, color=self.CN, lw=2.0, label="n  (refractive index)")
        an.set_ylabel("n", color=self.CN, fontsize=10)
        an.legend(loc="upper right", fontsize=9, facecolor=self.t["plot_ax"],
                  labelcolor=self.t["t1"], edgecolor=self.t["plot_grid"], framealpha=0.95)
        an.set_xlim(wl[0], wl[-1])
        if has_k:
            an.tick_params(labelbottom=False)
            self._sax(ak)
            ak.plot(wl, kv, color=self.CK, lw=2.0, label="k  (extinction)")
            ak.set_ylabel("k", color=self.CK, fontsize=10)
            ak.set_xlabel("Wavelength (nm)", color=self.t["t2"], fontsize=10, labelpad=5)
            ak.legend(loc="upper right", fontsize=9, facecolor=self.t["plot_ax"],
                      labelcolor=self.t["t1"], edgecolor=self.t["plot_grid"], framealpha=0.95)
            ak.set_xlim(wl[0], wl[-1])
        else:
            an.set_xlabel("Wavelength (nm)", color=self.t["t2"], fontsize=10, labelpad=5)
        pages = db.list_pages(mat.name)
        pg = pages[0][0] if pages else "built-in"
        self.fig.suptitle(f"{mat.name}   ·   {pg}   ·   {wl0:.0f}–{wl1:.0f} nm",
                          color=self.t["t2"], fontsize=9, x=0.5, y=0.97, ha="center")
        self.draw()


class StackCanvas(FigureCanvas):
    def __init__(self, t, parent=None):
        self.t = t
        self.fig = Figure(facecolor=t["plot_bg"])
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._st = self._db = None; self._empty()

    def apply_theme(self, t):
        self.t = t; self.fig.set_facecolor(t["plot_bg"])
        if self._st: self.plot(self._st, self._db)
        else: self._empty()

    def _empty(self):
        self.fig.clear(); self.fig.set_facecolor(self.t["plot_bg"])
        ax = self.fig.add_subplot(111, facecolor=self.t["plot_bg"]); ax.axis("off")
        ax.text(0.5, 0.5, "No layers defined", transform=ax.transAxes,
                ha="center", va="center", color=self.t["t2"], fontsize=11)
        self.draw()

    def plot(self, structure, db):
        self._st = structure; self._db = db
        self.fig.clear(); self.fig.set_facecolor(self.t["plot_bg"])
        layers = (
            [("incident", structure.incident, None)] +
            [(f"L{i+1}", l.material, l.thickness)
             for i, l in enumerate(structure.layers)] +
            [("substrate", structure.substrate, None)])
        n = len(layers)
        ax = self.fig.add_subplot(111, facecolor=self.t["plot_bg"])
        ax.set_xlim(0, 1); ax.set_ylim(-0.1, n+0.4); ax.axis("off")
        is_dark_theme = self.t is DARK
        for i, (role, mat, thick) in enumerate(reversed(layers)):
            is_film = role not in ("incident", "substrate")
            try:
                k = mat.N_at(550).imag
                if not is_film:
                    color = self.t["input"]
                elif k > 0.1:
                    color = "#3A2A08" if is_dark_theme else "#FFF3CD"
                else:
                    color = "#08354A" if is_dark_theme else "#D0EAFF"
            except:
                color = self.t["input"]
            alpha = 0.95 if is_film else 0.5
            edge  = self.t["accent"] if is_film else self.t["line1"]
            lw    = 1.0 if is_film else 0.5
            rect  = mpatches.FancyBboxPatch(
                (0.03, i+0.06), 0.94, 0.85,
                boxstyle="round,pad=0.012",
                facecolor=color, edgecolor=edge,
                linewidth=lw, alpha=alpha, zorder=2)
            ax.add_patch(rect)
            try: nv = mat.N_at(550).real
            except: nv = 0.0
            label = (f"{mat.name}   n={nv:.3f}   d={thick:.0f} nm"
                     if thick is not None
                     else f"{mat.name}   n={nv:.3f}   ({'incident' if role=='incident' else 'substrate'})")
            ax.text(0.5, i+0.47, label, ha="center", va="center",
                    color=self.t["t0"] if is_film else self.t["t1"],
                    fontsize=9,
                    fontweight="600" if is_film else "400",
                    zorder=3)
        ax.annotate("", xy=(0.5, n-0.2), xytext=(0.5, n+0.3),
                    arrowprops=dict(arrowstyle="-|>",
                                   color=self.t["accent"], lw=1.8), zorder=4)
        ax.text(0.5, n+0.32, "incident light", ha="center", va="bottom",
                color=self.t["accent"], fontsize=9, fontweight="600")
        self.fig.tight_layout(pad=0.3); self.draw()
