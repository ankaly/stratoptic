"""
Stratoptic - TMM Engine Test Suite
====================================
Author      : Necmeddin
Institution : Gazi University, Department of Photonics
Version     : 0.1.0

Test Cases
----------
1. Fresnel test     : Katmansız yapı — bilinen analitik çözümle karşılaştır
2. Quarter-wave test: Çeyrek dalga katman — minimum yansıma kontrolü
3. Brewster test    : p polarizasyonunda Brewster açısında R_p = 0
4. Energy test      : R + T + A = 1 tüm koşullarda
5. Angle test       : Açıya bağlı hesaplama tutarlılığı
"""

import sys
import numpy as np
sys.path.insert(0, 'motor')
from tmm import Material, Layer, Structure, TMMEngine, Polarization

# ─────────────────────────────────────────────────────────────
# Yardımcı fonksiyonlar
# ─────────────────────────────────────────────────────────────

def assert_close(value, expected, tol=1e-4, label=""):
    diff = abs(value - expected)
    status = "PASS" if diff < tol else "FAIL"
    print(f"  [{status}] {label}: {value:.6f} (beklenen ≈ {expected:.6f}, fark={diff:.2e})")
    return status == "PASS"

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ─────────────────────────────────────────────────────────────
# Ortak malzemeler
# ─────────────────────────────────────────────────────────────

air   = Material("Air",   1.000)
glass = Material("Glass", 1.520)
sio2  = Material("SiO2",  1.460)
tio2  = Material("TiO2",  2.350)

# ─────────────────────────────────────────────────────────────
# TEST 1: Fresnel — katmansız yapı
# ─────────────────────────────────────────────────────────────
# Normal incidenste hava/cam arayüzü için analitik Fresnel:
#   r = (n1 - n2) / (n1 + n2)
#   R = |r|^2

section("TEST 1: Fresnel — Katmansız Yapı (Hava → Cam)")

n1 = air.n
n2 = glass.n
R_fresnel = ((n1 - n2) / (n1 + n2)) ** 2
T_fresnel = 1.0 - R_fresnel

structure_bare = Structure(layers=[], incident=air, substrate=glass)
engine_bare    = TMMEngine(structure_bare)
result_bare    = engine_bare.calculate(
    wavelengths  = np.array([550.0]),
    angle        = 0.0,
    polarization = Polarization.S
)

all_pass = True
all_pass &= assert_close(result_bare.R[0], R_fresnel, label="R (Fresnel)")
all_pass &= assert_close(result_bare.T[0], T_fresnel, label="T (Fresnel)")
all_pass &= assert_close(result_bare.A[0], 0.0,       label="A = 0 (kayıpsız)")

# ─────────────────────────────────────────────────────────────
# TEST 2: Çeyrek Dalga Katman — Anti-Reflektif Kaplama
# ─────────────────────────────────────────────────────────────
# Tek katman anti-reflektif kaplama koşulu:
#   n_coat = sqrt(n_inc * n_sub)
#   d = λ / (4 * n_coat)   →  minimum yansıma (ideal: R = 0)
#
# SiO2 (n=1.46) hava/cam için tam AR koşulunu sağlamaz
# (ideal: n_coat = sqrt(1.0 * 1.52) ≈ 1.233)
# ama yansımayı düşürdüğünü doğrulayabiliriz.

section("TEST 2: Çeyrek Dalga Katman — AR Kaplama")

wl_design = 550.0  # nm, tasarım dalga boyu
n_ideal   = np.sqrt(air.n * glass.n)   # ≈ 1.233
d_quarter = wl_design / (4 * sio2.n)   # SiO2 için çeyrek dalga kalınlığı

print(f"  İdeal AR indisi  : {n_ideal:.4f}")
print(f"  SiO2 indisi      : {sio2.n:.4f}")
print(f"  Çeyrek λ kalınlık: {d_quarter:.2f} nm")

structure_ar = Structure(
    layers    = [Layer(sio2, d_quarter)],
    incident  = air,
    substrate = glass
)
engine_ar = TMMEngine(structure_ar)
result_ar = engine_ar.calculate(
    wavelengths  = np.array([wl_design]),
    angle        = 0.0,
    polarization = Polarization.S
)

# SiO2 ile yansıma azalmalı (katmansız: ~%4.26 → katmanlı: daha az)
R_bare_550 = R_fresnel
R_ar_550   = result_ar.R[0]
print(f"  R (katmansız)    : {R_bare_550:.4f}")
print(f"  R (SiO2 AR)      : {R_ar_550:.4f}")
reduced = R_ar_550 < R_bare_550
print(f"  [{'PASS' if reduced else 'FAIL'}] AR katman yansımayı azaltıyor: {reduced}")
all_pass &= reduced

# İdeal AR malzeme ile tam sıfır kontrolü
n_ar_ideal  = Material("AR_ideal", float(n_ideal))
d_ar_ideal  = wl_design / (4 * n_ideal)
structure_ideal = Structure(
    layers    = [Layer(n_ar_ideal, d_ar_ideal)],
    incident  = air,
    substrate = glass
)
result_ideal = TMMEngine(structure_ideal).calculate(
    wavelengths  = np.array([wl_design]),
    angle        = 0.0,
    polarization = Polarization.S
)
all_pass &= assert_close(result_ideal.R[0], 0.0, tol=1e-6, label="R = 0 (ideal AR malzeme)")

# ─────────────────────────────────────────────────────────────
# TEST 3: Brewster Açısı — R_p = 0
# ─────────────────────────────────────────────────────────────
# Brewster açısı: tan(θ_B) = n2 / n1
# Bu açıda p polarizasyonu için R_p = 0

section("TEST 3: Brewster Açısı (Hava → Cam, p polarizasyonu)")

theta_B = np.degrees(np.arctan(glass.n / air.n))
print(f"  Brewster açısı: {theta_B:.4f}°")

structure_brewster = Structure(layers=[], incident=air, substrate=glass)
engine_brewster    = TMMEngine(structure_brewster)
result_brewster_p  = engine_brewster.calculate(
    wavelengths  = np.array([550.0]),
    angle        = theta_B,
    polarization = Polarization.P
)
result_brewster_s = engine_brewster.calculate(
    wavelengths  = np.array([550.0]),
    angle        = theta_B,
    polarization = Polarization.S
)

all_pass &= assert_close(result_brewster_p.R[0], 0.0, tol=1e-6, label="R_p = 0 (Brewster)")
print(f"  [INFO] R_s (Brewster açısında): {result_brewster_s.R[0]:.6f}  (sıfır olmamalı ✓)")

# ─────────────────────────────────────────────────────────────
# TEST 4: Enerji Korunumu — R + T + A = 1
# ─────────────────────────────────────────────────────────────

section("TEST 4: Enerji Korunumu — R + T + A = 1")

# Kayıplı malzeme (k > 0) ile test
chrome = Material("Cr", n=3.18, k=3.33)
structure_lossy = Structure(
    layers    = [Layer(chrome, 20.0)],
    incident  = air,
    substrate = glass
)
result_lossy = TMMEngine(structure_lossy).calculate(
    wavelengths  = np.linspace(400, 800, 50),
    angle        = 0.0,
    polarization = Polarization.S
)
conservation = np.allclose(result_lossy.R + result_lossy.T + result_lossy.A, 1.0, atol=1e-10)
print(f"  [{'PASS' if conservation else 'FAIL'}] Kayıplı malzeme: R+T+A=1 tüm λ'da")
all_pass &= conservation

# Farklı açılar
for ang in [0, 15, 30, 45, 60]:
    res = TMMEngine(structure_bare).calculate(
        wavelengths  = np.linspace(400, 800, 20),
        angle        = float(ang),
        polarization = Polarization.S
    )
    ok = np.allclose(res.R + res.T + res.A, 1.0, atol=1e-10)
    print(f"  [{'PASS' if ok else 'FAIL'}] Enerji korunumu @ {ang}°")
    all_pass &= ok

# ─────────────────────────────────────────────────────────────
# TEST 5: Açıya Bağlı — Yansıma Artar
# ─────────────────────────────────────────────────────────────

section("TEST 5: Açıya Bağlı Hesaplama — Yüksek Açıda R Artar")

angles  = [0, 20, 40, 60, 80]
results = []
for ang in angles:
    res = TMMEngine(structure_bare).calculate(
        wavelengths  = np.array([550.0]),
        angle        = float(ang),
        polarization = Polarization.S
    )
    results.append(res.R[0])
    print(f"  θ = {ang:2d}°  →  R_s = {res.R[0]:.4f}")

monoton = all(results[i] <= results[i+1] for i in range(len(results)-1))
print(f"  [{'PASS' if monoton else 'FAIL'}] s pol: yansıma açıyla monoton artıyor")
all_pass &= monoton

# ─────────────────────────────────────────────────────────────
# SONUÇ
# ─────────────────────────────────────────────────────────────

section("SONUÇ")
if all_pass:
    print("  ✅ Tüm testler PASS — TMM motoru doğrulandı.")
else:
    print("  ❌ Bazı testler FAIL — kontrol gerekiyor.")
