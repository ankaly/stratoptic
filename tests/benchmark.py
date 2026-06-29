"""
Stratoptic — TMM performance benchmark.

Usage:
    python tests/benchmark.py                  # run, compare against baseline
    python tests/benchmark.py --save-baseline   # overwrite baseline with current run

Matrix is (n_points x n_layers). Layers alternate SiO2(100nm)/TiO2(80nm) on
Air/Glass_BK7, coherent stack (the path motor/engine.py vectorizes).
"""
import sys, time, json, argparse
import numpy as np

sys.path.insert(0, ".")
from motor.engine import TMMEngine, Layer, Structure
from motor.rii_db import RIIDatabase

BASELINE_PATH = "tests/benchmark_baseline.json"
REGRESSION_THRESHOLD = 1.20  # flag if current run is >20% slower than baseline

# Hard perf targets — independent of baseline, must always hold.
TARGETS_MS = {
    "500pt_5layer":    10.0,
    "10000pt_50layer": 200.0,
}

POINTS = [500, 1000, 5000, 10000]
LAYER_COUNTS = [1, 5, 10, 20, 50]

REPEATS = 10


def make_layers(db, n_layers):
    sio2, tio2 = db.get("SiO2"), db.get("TiO2")
    layers = []
    for i in range(n_layers):
        mat, d = (sio2, 100.0) if i % 2 == 0 else (tio2, 80.0)
        layers.append(Layer(mat, d))
    return layers


def run_matrix():
    db = RIIDatabase("data/rii_db")
    air, bk7 = db.get("Air"), db.get("Glass_BK7")
    results = {}

    for n_layers in LAYER_COUNTS:
        layers = make_layers(db, n_layers)
        st = Structure(layers=layers, incident=air, substrate=bk7,
                       substrate_coherent=True)
        eng = TMMEngine(st)
        for n_pts in POINTS:
            wl = np.linspace(380, 800, n_pts)
            times = []
            for _ in range(REPEATS):
                t0 = time.perf_counter()
                eng.calculate(wl, polarization="s")
                times.append(time.perf_counter() - t0)
            key = f"{n_pts}pt_{n_layers}layer"
            results[key] = round(float(np.mean(times) * 1000), 3)

    return results


def load_baseline():
    try:
        with open(BASELINE_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-baseline", action="store_true")
    args = parser.parse_args()

    results = run_matrix()

    if args.save_baseline:
        with open(BASELINE_PATH, "w") as f:
            json.dump(results, f, indent=2, sort_keys=True)
        print(f"Baseline saved to {BASELINE_PATH}")
        return

    baseline = load_baseline()
    failed = False

    print(f"{'scenario':22s} {'ms':>10s} {'baseline':>10s} {'delta':>8s}")
    for key in sorted(results, key=lambda k: (int(k.split('pt_')[0]),
                                              int(k.split('_')[1].rstrip('layer')))):
        ms = results[key]
        base = baseline.get(key)
        if base is None:
            delta_str = "  (new)"
        else:
            delta_pct = (ms / base - 1) * 100
            delta_str = f"{delta_pct:+6.1f}%"
            if ms > base * REGRESSION_THRESHOLD:
                delta_str += "  REGRESSION"
                failed = True
        print(f"{key:22s} {ms:10.2f} {('' if base is None else f'{base:.2f}'):>10s} {delta_str:>8s}")

    print()
    for key, target in TARGETS_MS.items():
        ms = results.get(key)
        status = "OK" if ms is not None and ms < target else "MISS"
        if status == "MISS":
            failed = True
        print(f"target {key:22s}: {ms:.2f} ms < {target} ms  [{status}]")

    if not baseline:
        print(f"\nNo baseline found at {BASELINE_PATH} — run with --save-baseline to create one.")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
