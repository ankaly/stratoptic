import sys, time
import numpy as np

sys.path.insert(0, ".")
from motor.engine import TMMEngine, Layer, Structure
from motor.rii_db import RIIDatabase

db = RIIDatabase("data/rii_db")

scenarios = [
    ("2-layer AR",  [("SiO2", 120), ("TiO2", 80)],  500),
    ("4-layer AR",  [("SiO2",100),("TiO2",50),("SiO2",120),("TiO2",80)], 500),
    ("10-layer",    [("SiO2",100),("TiO2",50)]*5, 500),
    ("High-res",    [("SiO2",120),("TiO2",80)], 5000),
    ("Metal",       [("Ag", 50)], 500),
]

for name, layers_spec, n_pts in scenarios:
    layers = [Layer(db.get(m), d) for m, d in layers_spec]
    st = Structure(layers=layers, incident=db.get("Air"), substrate=db.get("Glass_BK7"))
    wl = np.linspace(380, 800, n_pts)

    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        TMMEngine(st).calculate(wl, polarization="s")
        times.append(time.perf_counter() - t0)

    avg = np.mean(times) * 1000
    std = np.std(times) * 1000
    print(f"{name:20s}: {avg:8.1f} ± {std:.1f} ms  ({n_pts} pts)")
