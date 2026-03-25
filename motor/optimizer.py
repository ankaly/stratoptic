import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from engine import TMMEngine


class OptimizeWorker(QThread):
    finished = pyqtSignal(list, float)
    progress = pyqtSignal(str)

    def __init__(self, sf, oi, bounds, conditions, pol, angle):
        super().__init__()
        self._sf = sf; self._oi = oi; self._b = bounds
        self._cond = conditions; self._pol = pol; self._ang = angle

    def _cost(self, d):
        st = self._sf(self._oi, d); total = 0.0
        for wl0, wl1, metric, goal, weight in self._cond:
            wl = np.linspace(wl0, wl1, 150)
            r = TMMEngine(st).calculate(wl, angle=self._ang,
                                         polarization=self._pol,
                                         substrate_thickness_mm=1.0)
            val = {"R": r.R, "T": r.T, "A": r.A}[metric].mean()
            total += weight * (-val if goal == "max" else val)
        return total

    def run(self):
        from scipy.optimize import differential_evolution
        self.progress.emit("Optimizing…")
        res = differential_evolution(
            self._cost, bounds=self._b,
            maxiter=300, tol=1e-4, seed=42, workers=1, popsize=12)
        self.finished.emit(list(res.x), float(res.fun))
