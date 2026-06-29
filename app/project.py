"""
Stratoptic — project save/load (.strat format)

The on-disk format is plain JSON (see ROADMAP 6.1 for the schema). User-
loaded materials are embedded as raw [wl_nm, n, k] rows so a .strat file
is portable across machines without the original dataset file.
"""
import json
from datetime import datetime, timezone

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox

FORMAT_VERSION = 1


def to_dict(name, sidebar, ribbon, db, user_datasets):
    layers = []
    for r in range(sidebar.layer_table.rowCount()):
        item = sidebar.layer_table.item(r, 0)
        dataset = item.data(Qt.ItemDataRole.UserRole) or "default"
        d = float(sidebar.layer_table.item(r, 1).text())
        w = sidebar.layer_table.cellWidget(r, 2)
        chk = w.findChild(QCheckBox) if w else None
        layers.append({
            "material": item.text(),
            "dataset": dataset,
            "d_nm": d,
            "optimize": bool(chk and chk.isChecked()),
        })

    conditions = []
    for r in range(sidebar.cond_table.rowCount()):
        conditions.append({
            "wl_min": float(sidebar.cond_table.item(r, 0).text()),
            "wl_max": float(sidebar.cond_table.item(r, 1).text()),
            "metric": sidebar.cond_table.item(r, 2).text(),
            "goal":   sidebar.cond_table.item(r, 3).text(),
            "weight": float(sidebar.cond_table.item(r, 4).text()),
        })

    user_materials = []
    for uname in user_datasets:
        try:
            user_materials.append({
                "name": uname,
                "data": db.get(uname).export_raw_data(),
            })
        except Exception:
            pass  # material failed to (re)load — skip rather than abort the save

    return {
        "format_version": FORMAT_VERSION,
        "name": name,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "incident": sidebar.combo_inc.currentText(),
        "substrate": {"material": sidebar.combo_sub.currentText(), "dataset": "default"},
        "layers": layers,
        "params": {
            "wl_min": ribbon.spin_wl_min.value(),
            "wl_max": ribbon.spin_wl_max.value(),
            "points": ribbon.spin_pts.value(),
            "angle":  ribbon.spin_angle.value(),
            "pol":    ribbon.combo_pol.currentText(),
            "thick_substrate": sidebar.chk_thick_substrate.isChecked(),
        },
        "conditions": conditions,
        "user_materials": user_materials,
    }


def _migrate(data: dict) -> dict:
    version = data.get("format_version", 1)
    if version > FORMAT_VERSION:
        raise ValueError(
            f"Project format_version={version} is newer than this Stratoptic "
            f"build supports ({FORMAT_VERSION}). Update the app.")
    # No migrations exist yet — only format_version 1 has ever shipped.
    return data


def from_dict(data, sidebar, ribbon, db, user_datasets, status_bar=None):
    data = _migrate(data)
    combos = [sidebar.combo_mat, sidebar.combo_inc, sidebar.combo_sub]

    for um in data.get("user_materials", []):
        uname = um["name"]
        if uname in user_datasets and status_bar:
            status_bar.showMessage(
                f"Project's '{uname}' overwrites the already-loaded material of the same name.")
        db.register_user_material(uname, um["data"])
        if uname not in user_datasets:
            user_datasets.append(uname)
            for combo in combos:
                combo.addItem(uname)

    sidebar.clear_all()
    sidebar.set_incident(data["incident"])
    sidebar.set_substrate(data["substrate"]["material"])

    for L in data.get("layers", []):
        dataset = L.get("dataset") or "default"
        page = None if dataset == "default" else dataset
        sidebar.add_layer_row(L["material"], page, L["d_nm"], L.get("optimize", False))

    for c in data.get("conditions", []):
        sidebar.add_condition_row(c["wl_min"], c["wl_max"], c["metric"], c["goal"], c["weight"])

    p = data.get("params", {})
    if "wl_min" in p: ribbon.spin_wl_min.setValue(p["wl_min"])
    if "wl_max" in p: ribbon.spin_wl_max.setValue(p["wl_max"])
    if "points" in p: ribbon.spin_pts.setValue(p["points"])
    if "angle"  in p: ribbon.spin_angle.setValue(p["angle"])
    if "pol" in p:
        idx = ribbon.combo_pol.findText(p["pol"])
        if idx >= 0:
            ribbon.combo_pol.setCurrentIndex(idx)
    sidebar.chk_thick_substrate.setChecked(p.get("thick_substrate", True))

    sidebar.stack_refresh_requested.emit()
    return data.get("name", "Untitled")


def save(path, name, sidebar, ribbon, db, user_datasets):
    data = to_dict(name, sidebar, ribbon, db, user_datasets)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def load(path, sidebar, ribbon, db, user_datasets, status_bar=None):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return from_dict(data, sidebar, ribbon, db, user_datasets, status_bar)
