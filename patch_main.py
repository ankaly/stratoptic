"""
Stratoptic main.py patch — eski motor → yeni engine + rii_db
Çalıştır: python3 patch_main.py
"""

import re

path = "main.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

original = content

# ── 1. Import satırları ───────────────────────────────────────────────────
content = content.replace(
    "from tmm import Material, Layer, Structure, TMMEngine, Polarization\n"
    "from material_db import MaterialDatabase",
    "from rii_db import RIIDatabase\n"
    "from engine import Layer, Structure, TMMEngine"
)

# ── 2. DB başlatma ────────────────────────────────────────────────────────
content = content.replace(
    'self.db = MaterialDatabase("motor/materials.json")',
    'self.db = RIIDatabase("data/rii_db")'
)

# ── 3. Malzeme listesi (combo doldurma) ───────────────────────────────────
content = content.replace(
    "mats = sorted([k for k in self.db._materials\n"
    "                       if k not in (\"Air\",)])",
    "mats = sorted([k for k in self.db._index if k not in ('air',)])"
)

# ── 4. Incident / substrate combo'ları ────────────────────────────────────
# Incident
content = content.replace(
    'for m in ["Air", "Quartz"]:\n            self.combo_incident.addItem(m)',
    'for m in ["Air", "SiO2", "Glass_BK7"]:\n            self.combo_incident.addItem(m)'
)
# Substrate
content = content.replace(
    'for m in ["Glass_BK7", "Glass_Soda", "Quartz", "Si"]:\n            self.combo_substrate.addItem(m)',
    'for m in ["Glass_BK7", "SiO2", "Al2O3", "CaF2"]:\n            self.combo_substrate.addItem(m)'
)

# ── 5. _build_structure ───────────────────────────────────────────────────
content = content.replace(
    "        incident  = self.db.get(self.combo_incident.currentText())\n"
    "        substrate = self.db.get(self.combo_substrate.currentText())",
    "        incident  = self.db.get(self.combo_incident.currentText())\n"
    "        substrate = self.db.get(self.combo_substrate.currentText())\n"
    "        substrate.incoherent = True  # 1mm glass — incoherent"
)

content = content.replace(
    "        return Structure(layers=layers, incident=incident, substrate=substrate)",
    "        return Structure(layers=layers, incident=incident,\n"
    "                         substrate=substrate, substrate_coherent=False)"
)

# ── 6. Polarization sabitleri → string ────────────────────────────────────
content = content.replace("return Polarization.S", "return 's'")
content = content.replace("return Polarization.P", "return 'p'")
content = content.replace("return Polarization.ELLIPTIC", "return 'unpolarized'")

# ── 7. TMMEngine çağrısı ──────────────────────────────────────────────────
content = content.replace(
    "            engine = TMMEngine(structure)\n"
    "            result = engine.calculate(wl, angle=angle, polarization=pol)",
    "            engine = TMMEngine(structure)\n"
    "            result = engine.calculate(wl, angle=angle, polarization=pol,\n"
    "                                       substrate_thickness_mm=1.0)"
)

# ── 8. Material Database dialog ───────────────────────────────────────────
content = content.replace(
    "        lines = []\n"
    "        for key, entry in self.db._materials.items():\n"
    "            lines.append(\n"
    "                f\"{entry['name']:<14} n={entry['n']:<6} \"\n"
    "                f\"k={entry.get('k',0.0):<6} [{entry.get('category','—')}]\"\n"
    "            )\n"
    "        QMessageBox.information(self, \"Material Database\",\n"
    "                                \"\\n\".join(lines))",
    "        lines = [f\"{m.name:<18} n@550={m.n_ref:.4f}  k@550={m.k_ref:.4f}\"\n"
    "                 for mats in list(self.db._index.values())[:40]\n"
    "                 for m in mats[:1]]\n"
    "        QMessageBox.information(self, \"Material Database\",\n"
    "                                \"\\n\".join(lines))"
)

# ── 9. stack_canvas.plot — db argümanı kaldır ─────────────────────────────
# StackCanvas.plot(structure, db) → plot(structure, self.db) zaten var, sorun yok

if content == original:
    print("UYARI: Hiçbir değişiklik yapılmadı — pattern'lar eşleşmedi.")
    print("Manuel kontrol gerekebilir.")
else:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("main.py başarıyla güncellendi.")
    print("Değişiklikler:")
    print("  ✓ Import satırları")
    print("  ✓ RIIDatabase başlatma")
    print("  ✓ Malzeme listesi")
    print("  ✓ Combo malzemeleri")
    print("  ✓ _build_structure")
    print("  ✓ Polarization sabitleri")
    print("  ✓ TMMEngine çağrısı")
    print("  ✓ Material Database dialog")
