"""
Stratoptic main.py patch — dinamik malzeme comboları
Çalıştır: python3 patch_combos.py
"""

path = "main.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

original = content

# ── 1. Incident combo ─────────────────────────────────────────────────────
old_incident = (
    'for m in ["Air", "SiO2", "Glass_BK7"]:\n'
    '            self.combo_incident.addItem(m)'
)
new_incident = (
    '# Incident: düşük n (<1.8), şeffaf malzemeler\n'
    '            incident_mats = ["Air", "Vacuum", "SiO2", "MgF2",\n'
    '                             "Al2O3", "CaF2", "Glass_BK7"]\n'
    '            # RII\'den ekstra şeffaf malzemeler\n'
    '            for key, mats in sorted(self.db._index.items()):\n'
    '                m = mats[0]\n'
    '                try:\n'
    '                    N = m.N_at(550)\n'
    '                    if N.imag < 0.001 and 1.0 < N.real < 2.0:\n'
    '                        name = m.name\n'
    '                        if name not in incident_mats:\n'
    '                            incident_mats.append(name)\n'
    '                except Exception:\n'
    '                    pass\n'
    '            for m in incident_mats[:40]:\n'
    '                self.combo_incident.addItem(m)'
)

# ── 2. Substrate combo ────────────────────────────────────────────────────
old_substrate = (
    'for m in ["Glass_BK7", "SiO2", "Al2O3", "CaF2"]:\n'
    '            self.combo_substrate.addItem(m)'
)
new_substrate = (
    '# Substrate: şeffaf malzemeler\n'
    '            substrate_mats = ["Glass_BK7", "SiO2", "Al2O3",\n'
    '                              "CaF2", "MgF2", "TiO2"]\n'
    '            for key, mats in sorted(self.db._index.items()):\n'
    '                m = mats[0]\n'
    '                try:\n'
    '                    N = m.N_at(550)\n'
    '                    if N.imag < 0.01 and N.real > 1.0:\n'
    '                        name = m.name\n'
    '                        if name not in substrate_mats:\n'
    '                            substrate_mats.append(name)\n'
    '                except Exception:\n'
    '                    pass\n'
    '            for m in substrate_mats[:80]:\n'
    '                self.combo_substrate.addItem(m)'
)

# ── 3. Layer material combo ───────────────────────────────────────────────
old_layers = (
    'mats = sorted([k for k in self.db._index if k not in (\'air\',)])'
)
new_layers = (
    '# Tüm malzemeler — katman için\n'
    '            mats = []\n'
    '            priority = ["TiO2", "SiO2", "Ag", "Au", "Al", "Cr",\n'
    '                        "MgF2", "Al2O3", "HfO2", "Ta2O5", "ZnO",\n'
    '                        "Si3N4", "ITO", "Cu"]\n'
    '            for p in priority:\n'
    '                if p.lower() in self.db._index:\n'
    '                    mats.append(p)\n'
    '            for key in sorted(self.db._index.keys()):\n'
    '                name = self.db._index[key][0].name\n'
    '                if name not in mats and key not in ("air", "vacuum"):\n'
    '                    mats.append(name)'
)

found = []
for old, new, label in [
    (old_incident,  new_incident,  "Incident combo"),
    (old_substrate, new_substrate, "Substrate combo"),
    (old_layers,    new_layers,    "Layer combo"),
]:
    if old in content:
        content = content.replace(old, new)
        found.append(label)
    else:
        print(f"  ✗ Bulunamadı: {label}")

if content != original:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    for f_label in found:
        print(f"  ✓ {f_label}")
    print("Tamamlandı.")
else:
    print("Hiçbir değişiklik yapılmadı.")
