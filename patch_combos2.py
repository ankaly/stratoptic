"""
Stratoptic main.py patch — combo girinti düzeltme
Çalıştır: python3 patch_combos2.py
"""

path = "main.py"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Bul ve değiştir — satır bazlı
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]

    # ── Incident combo bloğunu bul ────────────────────────────────────────
    if '# Incident: düşük n (<1.8), şeffaf malzemeler' in line:
        # Bu bloğun başındaki indentasyonu al
        indent = len(line) - len(line.lstrip())
        ind = ' ' * indent
        # Bloğun sonuna kadar atla
        while i < len(lines) and 'self.combo_incident.addItem(m)' not in lines[i]:
            i += 1
        i += 1  # addItem satırını da atla
        # Yeni temiz blok yaz
        new_lines.append(f'{ind}for m in ["Air", "Vacuum", "SiO2", "MgF2",\n')
        new_lines.append(f'{ind}          "Al2O3", "CaF2", "Glass_BK7",\n')
        new_lines.append(f'{ind}          "TiO2", "ZnO", "Si3N4"]:\n')
        new_lines.append(f'{ind}    self.combo_incident.addItem(m)\n')
        new_lines.append(f'{ind}# RII\'den şeffaf malzemeler\n')
        new_lines.append(f'{ind}for key, mats in sorted(self.db._index.items()):\n')
        new_lines.append(f'{ind}    try:\n')
        new_lines.append(f'{ind}        N = mats[0].N_at(550)\n')
        new_lines.append(f'{ind}        if (N.imag < 0.001 and 1.0 < N.real < 2.0\n')
        new_lines.append(f'{ind}                and mats[0].name not in\n')
        new_lines.append(f'{ind}                [self.combo_incident.itemText(j)\n')
        new_lines.append(f'{ind}                 for j in range(self.combo_incident.count())]):\n')
        new_lines.append(f'{ind}            self.combo_incident.addItem(mats[0].name)\n')
        new_lines.append(f'{ind}    except Exception:\n')
        new_lines.append(f'{ind}        pass\n')
        continue

    # ── Substrate combo bloğunu bul ───────────────────────────────────────
    elif '# Substrate: şeffaf malzemeler' in line:
        indent = len(line) - len(line.lstrip())
        ind = ' ' * indent
        while i < len(lines) and 'self.combo_substrate.addItem(m)' not in lines[i]:
            i += 1
        i += 1
        new_lines.append(f'{ind}for m in ["Glass_BK7", "SiO2", "Al2O3",\n')
        new_lines.append(f'{ind}          "CaF2", "MgF2", "TiO2", "Quartz"]:\n')
        new_lines.append(f'{ind}    self.combo_substrate.addItem(m)\n')
        new_lines.append(f'{ind}for key, mats in sorted(self.db._index.items()):\n')
        new_lines.append(f'{ind}    try:\n')
        new_lines.append(f'{ind}        N = mats[0].N_at(550)\n')
        new_lines.append(f'{ind}        if (N.imag < 0.01 and N.real > 1.0\n')
        new_lines.append(f'{ind}                and mats[0].name not in\n')
        new_lines.append(f'{ind}                [self.combo_substrate.itemText(j)\n')
        new_lines.append(f'{ind}                 for j in range(self.combo_substrate.count())]):\n')
        new_lines.append(f'{ind}            self.combo_substrate.addItem(mats[0].name)\n')
        new_lines.append(f'{ind}    except Exception:\n')
        new_lines.append(f'{ind}        pass\n')
        continue

    # ── Layer combo bloğunu bul ───────────────────────────────────────────
    elif '# Tüm malzemeler — katman için' in line:
        indent = len(line) - len(line.lstrip())
        ind = ' ' * indent
        while i < len(lines) and 'mats.append(name)' in lines[i] or \
              (i < len(lines) and ('mats = []' in lines[i] or
               'priority' in lines[i] or 'for p in' in lines[i] or
               'for key in' in lines[i] or 'if name not in' in lines[i])):
            i += 1
            if i >= len(lines):
                break
        new_lines.append(f'{ind}priority = ["TiO2", "SiO2", "Ag", "Au", "Al",\n')
        new_lines.append(f'{ind}            "Cr", "MgF2", "Al2O3", "HfO2",\n')
        new_lines.append(f'{ind}            "Ta2O5", "ZnO", "Si3N4", "Cu"]\n')
        new_lines.append(f'{ind}mats = [p for p in priority\n')
        new_lines.append(f'{ind}        if p.lower() in self.db._index]\n')
        new_lines.append(f'{ind}for key in sorted(self.db._index.keys()):\n')
        new_lines.append(f'{ind}    name = self.db._index[key][0].name\n')
        new_lines.append(f'{ind}    if name not in mats and key not in ("air","vacuum"):\n')
        new_lines.append(f'{ind}        mats.append(name)\n')
        continue

    new_lines.append(line)
    i += 1

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Tamamlandı.")
