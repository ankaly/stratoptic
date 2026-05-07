import numpy as np
from PyQt6.QtWidgets import (
    QFileDialog, QMessageBox, QInputDialog,
    QDialog, QVBoxLayout, QLabel, QListWidget,
    QPushButton, QDialogButtonBox,
)


def export_png(parent, result, canvas):
    if not result:
        return
    path, _ = QFileDialog.getSaveFileName(
        parent, "Export", "spectrum.png", "PNG (*.png);;PDF (*.pdf)")
    if path:
        canvas.save(path)


def export_csv(parent, result):
    if not result:
        return
    path, _ = QFileDialog.getSaveFileName(
        parent, "Export CSV", "spectrum.csv", "CSV (*.csv)")
    if path:
        np.savetxt(path, np.column_stack([result.wavelengths, result.R, result.T, result.A]),
                   delimiter=",", header="wavelength_nm,R,T,A", comments="")


def import_dataset(parent, db, combos, user_datasets, status_bar):
    fmt_msg = (
        "<b>Supported formats:</b> CSV, TXT, DAT<br><br>"
        "<b>Required columns:</b><br>"
        "&nbsp;&nbsp;wavelength &nbsp; n &nbsp; [k]<br><br>"
        "<b>Wavelength unit:</b> nm (auto-detected — if max &lt; 50, assumed µm)<br>"
        "<b>Separator:</b> comma, semicolon, tab, or space<br>"
        "<b>Header lines:</b> skip lines starting with <code>#</code> or non-numeric<br>"
        "<b>Minimum:</b> 3 data points<br><br>"
        "<b>Example (CSV):</b><br>"
        "<code>wavelength_nm,n,k<br>"
        "400,2.35,0.0<br>"
        "500,2.31,0.0<br>"
        "600,2.28,0.0</code>"
    )
    info = QMessageBox(parent)
    info.setWindowTitle("Import Format")
    info.setText(fmt_msg)
    info.setIcon(QMessageBox.Icon.Information)
    info.setStandardButtons(
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
    info.button(QMessageBox.StandardButton.Ok).setText("Choose File…")
    if info.exec() != QMessageBox.StandardButton.Ok:
        return

    path, _ = QFileDialog.getOpenFileName(
        parent, "Import Material Dataset", "",
        "CSV/TXT (*.csv *.txt *.dat);;All files (*)")
    if not path:
        return
    name, ok = QInputDialog.getText(parent, "Material Name",
                                    "Enter a name for this material:")
    if not ok or not name.strip():
        return
    name = name.strip()
    try:
        mat = db.load_user_dataset(path, name)
    except Exception as e:
        QMessageBox.warning(parent, "Import Failed", str(e))
        return

    wl0, wl1 = mat._wl_range
    try:
        n_pts = len(mat._interp_n.x)
    except Exception:
        n_pts = 0

    for combo in combos:
        combo.addItem(name)

    user_datasets.append(name)
    status_bar.showMessage(
        f"Loaded: {name}  ({n_pts} points, {wl0:.0f}–{wl1:.0f} nm)")


def manage_datasets_dialog(parent, db, combos, user_datasets, status_bar):
    dlg = QDialog(parent)
    dlg.setWindowTitle("User Datasets")
    dlg.setMinimumWidth(320)
    vl = QVBoxLayout(dlg)
    vl.addWidget(QLabel("Imported materials:"))
    lst = QListWidget()
    for name in user_datasets:
        lst.addItem(name)
    vl.addWidget(lst)

    btn_del = QPushButton("Delete selected")
    btn_del.setObjectName("rm")

    def _delete():
        row = lst.currentRow()
        if row < 0:
            return
        name = lst.item(row).text()
        key = name.lower()
        if key in db._index and db._index[key][0].shelf == "user":
            del db._index[key]
        user_datasets.remove(name)
        for combo in combos:
            idx = combo.findText(name)
            if idx >= 0:
                combo.removeItem(idx)
        lst.takeItem(row)
        status_bar.showMessage(f"Removed: {name}")

    btn_del.clicked.connect(_delete)
    vl.addWidget(btn_del)
    bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    bb.rejected.connect(dlg.reject)
    vl.addWidget(bb)
    dlg.exec()


def show_db_dialog(parent, db):
    lines = [f"{mats[0].name:<18} n@550={mats[0].n_ref:.4f}  k@550={mats[0].k_ref:.4f}"
             for mats in list(db._index.values())[:50]]
    QMessageBox.information(parent, "Material Database", "\n".join(lines))


def show_about_dialog(parent):
    QMessageBox.about(parent, "About Stratoptic",
        "Stratoptic v1.0\n\nThin Film Design & Simulation Platform\n"
        "Byrnes (2021) TMM + RefractiveIndex.info DB\n\n"
        "Author: Necmeddin\n"
        "Gazi University Photonics Research Center\n\n"
        "Byrnes, arXiv:1603.02720 (2021)\n"
        "Johnson & Christy, Phys. Rev. B 6 (1972)\n"
        "Born & Wolf, Principles of Optics (1999)")
