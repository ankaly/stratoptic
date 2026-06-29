from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QDoubleSpinBox, QSpinBox,
    QSizePolicy, QCheckBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt, pyqtSignal

from motor.engine import Layer, Structure
from ui.theme import sec, muted, hdiv


class Sidebar(QWidget):

    status_message = pyqtSignal(str)
    dispersion_requested = pyqtSignal(object)
    stack_refresh_requested = pyqtSignal()
    project_changed = pyqtSignal()

    def __init__(self, theme, db):
        super().__init__()
        self.db = db
        self._t = theme
        self.setObjectName("sidebar")
        self.setMinimumWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Preferred,
                           QSizePolicy.Policy.Expanding)
        ol = QVBoxLayout(self)
        ol.setContentsMargins(0, 0, 0, 0); ol.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(14, 14, 14, 14); il.setSpacing(14)

        # ── Incident ─────────────────────────────────────────────────
        il.addWidget(sec("Incident Medium"))
        self.combo_inc = QComboBox()
        self.combo_inc.addItem("— Select incident medium —")
        inc_fixed = ["Air", "Vacuum", "SiO2", "MgF2", "Al2O3", "CaF2", "Glass_BK7"]
        for m in inc_fixed:
            self.combo_inc.addItem(m)
        for key, mats in sorted(db._index.items()):
            try:
                N = mats[0].N_at(550); name = mats[0].name
                if N.imag < 0.001 and 1.0 < N.real < 2.0 and name not in inc_fixed:
                    self.combo_inc.addItem(name)
            except Exception:
                pass
        self.combo_inc.currentTextChanged.connect(lambda _: self.project_changed.emit())
        il.addWidget(self.combo_inc)
        il.addWidget(hdiv(theme))

        # ── Layers ───────────────────────────────────────────────────
        il.addWidget(sec("Layers"))

        add_r = QHBoxLayout(); add_r.setSpacing(6)
        self.combo_mat = QComboBox()
        self.combo_mat.addItem("— Select material —")
        priority = ["TiO2", "SiO2", "Ag", "Au", "Al", "Cr", "MgF2", "Al2O3",
                     "HfO2", "Ta2O5", "ZnO", "Si3N4", "Cu", "Pt"]
        mats_list = [p for p in priority if p.lower() in db._index]
        for key in sorted(db._index.keys()):
            name = db._index[key][0].name
            if name not in mats_list and key not in ("air", "vacuum"):
                mats_list.append(name)
        for m in mats_list:
            self.combo_mat.addItem(m)
        self.combo_mat.currentTextChanged.connect(self._update_dispersion)
        self.combo_mat.currentTextChanged.connect(self._update_page_list)

        self.spin_d = QDoubleSpinBox()
        self.spin_d.setRange(0.1, 50000); self.spin_d.setValue(100.0)
        self.spin_d.setDecimals(1); self.spin_d.setSuffix(" nm")
        self.spin_d.setFixedWidth(92)

        btn_add = QPushButton("+ Add"); btn_add.setObjectName("ghost")
        btn_add.setFixedWidth(70); btn_add.setFixedHeight(28)
        btn_add.clicked.connect(self._add_layer)

        add_r.addWidget(self.combo_mat, 1)
        add_r.addWidget(self.spin_d)
        add_r.addWidget(btn_add)
        il.addLayout(add_r)

        # Dataset (page) selector
        page_r = QHBoxLayout(); page_r.setSpacing(6)
        page_r.addWidget(muted("Dataset:"))
        self.combo_page = QComboBox()
        self.combo_page.setEnabled(False)
        self.combo_page.currentTextChanged.connect(self._on_page_changed)
        page_r.addWidget(self.combo_page, 1)
        il.addLayout(page_r)

        self.lbl_dataset_info = QLabel("")
        self.lbl_dataset_info.setObjectName("muted")
        self.lbl_dataset_info.setWordWrap(True)
        il.addWidget(self.lbl_dataset_info)

        # Reorder buttons
        reorder_r = QHBoxLayout(); reorder_r.setSpacing(4)
        reorder_r.addStretch()
        btn_up = QPushButton("↑"); btn_up.setObjectName("ghost")
        btn_up.setFixedSize(30, 24); btn_up.setToolTip("Move layer up")
        btn_up.clicked.connect(self._move_layer_up)
        btn_down = QPushButton("↓"); btn_down.setObjectName("ghost")
        btn_down.setFixedSize(30, 24); btn_down.setToolTip("Move layer down")
        btn_down.clicked.connect(self._move_layer_down)
        reorder_r.addWidget(btn_up); reorder_r.addWidget(btn_down)
        il.addLayout(reorder_r)

        # Layer table
        self.layer_table = QTableWidget(0, 4)
        self.layer_table.setHorizontalHeaderLabels(["Material", "d (nm)", "Opt", ""])
        self.layer_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.layer_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self.layer_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed)
        self.layer_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed)
        self.layer_table.setColumnWidth(2, 36)
        self.layer_table.setColumnWidth(3, 30)
        self.layer_table.setAlternatingRowColors(True)
        self.layer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.layer_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.layer_table.verticalHeader().setVisible(False)
        self.layer_table.setMinimumHeight(100)
        self.layer_table.setMaximumHeight(260)
        self.layer_table.verticalHeader().setDefaultSectionSize(28)
        self.layer_table.cellChanged.connect(self._on_layer_edited)
        il.addWidget(self.layer_table)
        il.addWidget(hdiv(theme))

        # ── Substrate ────────────────────────────────────────────────
        il.addWidget(sec("Substrate"))
        self.combo_sub = QComboBox()
        self.combo_sub.addItem("— Select substrate —")
        sub_fixed = ["Glass_BK7", "SiO2", "Al2O3", "CaF2", "MgF2"]
        for m in sub_fixed:
            self.combo_sub.addItem(m)
        for key, ml in sorted(db._index.items()):
            try:
                N = ml[0].N_at(550); name = ml[0].name
                if N.imag < 0.01 and N.real > 1.0 and name not in sub_fixed:
                    self.combo_sub.addItem(name)
            except Exception:
                pass
        self.combo_sub.currentTextChanged.connect(lambda _: self.project_changed.emit())
        il.addWidget(self.combo_sub)
        il.addWidget(hdiv(theme))

        # ── Optimization Conditions ──────────────────────────────────
        il.addWidget(sec("Optimization Conditions"))

        self.cond_table = QTableWidget(0, 6)
        self.cond_table.setHorizontalHeaderLabels(
            ["λ min", "λ max", "Metric", "Goal", "Weight", ""])
        col_widths = [60, 60, 48, 44, 56, 28]
        for i, w in enumerate(col_widths):
            self.cond_table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.Fixed)
            self.cond_table.setColumnWidth(i, w)
        self.cond_table.setAlternatingRowColors(True)
        self.cond_table.verticalHeader().setVisible(False)
        self.cond_table.verticalHeader().setDefaultSectionSize(26)
        self.cond_table.setMinimumHeight(60)
        self.cond_table.setMaximumHeight(160)
        il.addWidget(self.cond_table)

        cr1 = QHBoxLayout(); cr1.setSpacing(6)
        cr1.addWidget(muted("λ:"))
        self.spin_cwl0 = QSpinBox(); self.spin_cwl0.setRange(100, 5000)
        self.spin_cwl0.setValue(380); self.spin_cwl0.setSuffix(" nm")
        d_lbl = muted("–"); d_lbl.setFixedWidth(8)
        d_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_cwl1 = QSpinBox(); self.spin_cwl1.setRange(100, 5000)
        self.spin_cwl1.setValue(700); self.spin_cwl1.setSuffix(" nm")
        cr1.addWidget(self.spin_cwl0, 1); cr1.addWidget(d_lbl)
        cr1.addWidget(self.spin_cwl1, 1)
        il.addLayout(cr1)

        cr2 = QHBoxLayout(); cr2.setSpacing(6)
        self.combo_cm = QComboBox(); self.combo_cm.addItems(["R", "T", "A"])
        self.combo_cm.setFixedWidth(54)
        self.combo_cg = QComboBox(); self.combo_cg.addItems(["max", "min"])
        self.combo_cg.setFixedWidth(60)
        self.spin_cw = QDoubleSpinBox()
        self.spin_cw.setRange(0.01, 10.0); self.spin_cw.setValue(1.0)
        self.spin_cw.setSingleStep(0.1); self.spin_cw.setFixedWidth(58)
        btn_cadd = QPushButton("+ Add"); btn_cadd.setObjectName("ghost")
        btn_cadd.setFixedHeight(28); btn_cadd.clicked.connect(self._add_cond)
        cr2.addWidget(self.combo_cm)
        cr2.addWidget(self.combo_cg)
        cr2.addWidget(self.spin_cw)
        cr2.addWidget(btn_cadd)
        il.addLayout(cr2)

        il.addStretch()
        scroll.setWidget(inner)
        ol.addWidget(scroll)

    # ── Layer management ─────────────────────────────────────────────

    def add_layer_row(self, material, dataset=None, thickness=100.0, optimize=False):
        """Append a layer row. `dataset` is a page/dataset name or None for
        the material's default. Used both by the "+ Add" button and by
        app/project.py when restoring a saved project."""
        row = self.layer_table.rowCount(); self.layer_table.insertRow(row)
        mat_item = QTableWidgetItem(material)
        mat_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        if dataset:
            mat_item.setData(Qt.ItemDataRole.UserRole, dataset)
            mat_item.setToolTip(f"Dataset: {dataset}")
        self.layer_table.setItem(row, 0, mat_item)
        self.layer_table.setItem(row, 1, QTableWidgetItem(f"{thickness:.1f}"))
        cw = QWidget(); cl = QHBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0); cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chk = QCheckBox(); chk.setChecked(optimize); cl.addWidget(chk)
        self.layer_table.setCellWidget(row, 2, cw)
        btn = QPushButton("✕"); btn.setObjectName("rm")
        btn.setFixedSize(26, 22); btn.clicked.connect(self._remove_layer)
        self.layer_table.setCellWidget(row, 3, btn)
        return row

    def clear_layers(self):
        self.layer_table.setRowCount(0)

    def _add_layer(self):
        mat = self.combo_mat.currentText()
        if mat.startswith("—"):
            self.status_message.emit("Please select a material first.")
            return
        page = self.combo_page.currentText() if self.combo_page.isEnabled() else None
        try:
            self.db.get(mat, page=page)
        except Exception as e:
            self.status_message.emit(f"Material error: {e}")
            return
        d = self.spin_d.value()
        self.add_layer_row(mat, page, d)
        self.stack_refresh_requested.emit()
        self.project_changed.emit()
        self.status_message.emit(f"Added: {mat}  {d:.1f} nm")

    def _remove_layer(self):
        btn = self.sender()
        for row in range(self.layer_table.rowCount()):
            if self.layer_table.cellWidget(row, 3) is btn:
                self.layer_table.removeRow(row); break
        self.stack_refresh_requested.emit()
        self.project_changed.emit()

    def _on_layer_edited(self, row, col):
        if col != 1:
            return
        item = self.layer_table.item(row, col)
        if item is None:
            return
        try:
            val = float(item.text())
            if val <= 0:
                raise ValueError
        except ValueError:
            self.layer_table.blockSignals(True)
            item.setText(f"{self.spin_d.value():.1f}")
            self.layer_table.blockSignals(False)
            return
        self.layer_table.blockSignals(True)
        item.setText(f"{val:.1f}")
        self.layer_table.blockSignals(False)
        self.stack_refresh_requested.emit()
        self.project_changed.emit()

    def _swap_rows(self, r1, r2):
        t = self.layer_table
        t.blockSignals(True)
        mat1 = t.item(r1, 0).text(); d1 = t.item(r1, 1).text()
        page1 = t.item(r1, 0).data(Qt.ItemDataRole.UserRole)
        opt1 = (w := t.cellWidget(r1, 2)) and (c := w.findChild(QCheckBox)) and c.isChecked()
        mat2 = t.item(r2, 0).text(); d2 = t.item(r2, 1).text()
        page2 = t.item(r2, 0).data(Qt.ItemDataRole.UserRole)
        opt2 = (w := t.cellWidget(r2, 2)) and (c := w.findChild(QCheckBox)) and c.isChecked()

        for row, mat, d, opt, page in [(r1, mat2, d2, opt2, page2),
                                        (r2, mat1, d1, opt1, page1)]:
            mi = QTableWidgetItem(mat)
            mi.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            if page:
                mi.setData(Qt.ItemDataRole.UserRole, page)
                mi.setToolTip(f"Dataset: {page}")
            t.setItem(row, 0, mi)
            t.setItem(row, 1, QTableWidgetItem(d))
            cw = QWidget(); cl = QHBoxLayout(cw)
            cl.setContentsMargins(0, 0, 0, 0); cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox(); chk.setChecked(opt); cl.addWidget(chk)
            t.setCellWidget(row, 2, cw)
            btn = QPushButton("✕"); btn.setObjectName("rm")
            btn.setFixedSize(26, 22); btn.clicked.connect(self._remove_layer)
            t.setCellWidget(row, 3, btn)
        t.blockSignals(False)

    def _move_layer_up(self):
        row = self.layer_table.currentRow()
        if row <= 0:
            return
        self._swap_rows(row - 1, row)
        self.layer_table.setCurrentCell(row - 1, 1)
        self.stack_refresh_requested.emit()
        self.project_changed.emit()

    def _move_layer_down(self):
        row = self.layer_table.currentRow()
        if row < 0 or row >= self.layer_table.rowCount() - 1:
            return
        self._swap_rows(row, row + 1)
        self.layer_table.setCurrentCell(row + 1, 1)
        self.stack_refresh_requested.emit()
        self.project_changed.emit()

    # ── Page / dispersion ────────────────────────────────────────────

    def _update_page_list(self, mat_name):
        self.combo_page.blockSignals(True)
        self.combo_page.clear()
        if mat_name.startswith("—"):
            self.combo_page.setEnabled(False)
            self.combo_page.blockSignals(False)
            return
        pages = self.db.list_pages(mat_name)
        if len(pages) <= 1:
            self.combo_page.setEnabled(False)
            self.combo_page.blockSignals(False)
            return
        self.combo_page.setEnabled(True)
        preferred_idx = 0
        for i, (page_name, yml_path) in enumerate(pages):
            self.combo_page.addItem(page_name)
            try:
                mat = self.db.get(mat_name, page=page_name)
                wl0, wl1 = mat.wl_range_nm
                self.combo_page.setItemData(i, f"λ: {wl0:.0f}–{wl1:.0f} nm",
                                            Qt.ItemDataRole.ToolTipRole)
            except Exception:
                pass
            if "johnson" in page_name.lower():
                preferred_idx = i
        self.combo_page.setCurrentIndex(preferred_idx)
        self.combo_page.blockSignals(False)

    def _on_page_changed(self, _):
        self._update_dispersion(self.combo_mat.currentText())

    def _update_dispersion(self, mat_name):
        if mat_name.startswith("—"):
            self.lbl_dataset_info.setText("")
            return
        try:
            page = self.combo_page.currentText() if self.combo_page.isEnabled() else None
            mat = self.db.get(mat_name, page=page)
            self.dispersion_requested.emit(mat)
            self._refresh_dataset_info(mat)
        except Exception:
            self.lbl_dataset_info.setText("")

    def _refresh_dataset_info(self, mat):
        try:
            wl0, wl1 = mat.wl_range_nm
            wl_str = f"λ: {wl0:.0f}–{wl1:.0f} nm"
            mat._load()
            if mat._formula is not None:
                data_str = "formula"
            elif mat._interp_k is not None:
                data_str = "tabulated nk"
            else:
                data_str = "tabulated n"
            page = mat.page or ""
            self.lbl_dataset_info.setText(f"{page}  |  {wl_str}  |  {data_str}")
        except Exception:
            self.lbl_dataset_info.setText("")

    # ── Conditions ───────────────────────────────────────────────────

    def add_condition_row(self, wl0, wl1, metric, goal, weight):
        row = self.cond_table.rowCount(); self.cond_table.insertRow(row)
        self.cond_table.setItem(row, 0, QTableWidgetItem(str(wl0)))
        self.cond_table.setItem(row, 1, QTableWidgetItem(str(wl1)))
        self.cond_table.setItem(row, 2, QTableWidgetItem(metric))
        self.cond_table.setItem(row, 3, QTableWidgetItem(goal))
        self.cond_table.setItem(row, 4, QTableWidgetItem(f"{weight:.2f}"))
        btn = QPushButton("✕"); btn.setObjectName("rm")
        btn.setFixedSize(22, 20); btn.clicked.connect(self._remove_cond)
        self.cond_table.setCellWidget(row, 5, btn)
        return row

    def clear_conditions(self):
        self.cond_table.setRowCount(0)

    def clear_all(self):
        self.clear_layers()
        self.clear_conditions()
        self.combo_inc.setCurrentIndex(0)
        self.combo_sub.setCurrentIndex(0)

    def _add_cond(self):
        wl0 = self.spin_cwl0.value(); wl1 = self.spin_cwl1.value()
        if wl0 >= wl1:
            self.status_message.emit("λ min must be < λ max")
            return
        self.add_condition_row(wl0, wl1, self.combo_cm.currentText(),
                               self.combo_cg.currentText(), self.spin_cw.value())
        self.project_changed.emit()

    def _remove_cond(self):
        btn = self.sender()
        for row in range(self.cond_table.rowCount()):
            if self.cond_table.cellWidget(row, 5) is btn:
                self.cond_table.removeRow(row); break
        self.project_changed.emit()

    # ── Public API ───────────────────────────────────────────────────

    def set_incident(self, name):
        idx = self.combo_inc.findText(name)
        self.combo_inc.setCurrentIndex(idx if idx >= 0 else 0)

    def set_substrate(self, name):
        idx = self.combo_sub.findText(name)
        self.combo_sub.setCurrentIndex(idx if idx >= 0 else 0)

    def get_opt_idx(self):
        return [r for r in range(self.layer_table.rowCount())
                if (w := self.layer_table.cellWidget(r, 2)) and
                   (c := w.findChild(QCheckBox)) and c.isChecked()]

    def build_structure(self):
        inc = self.combo_inc.currentText()
        sub = self.combo_sub.currentText()
        if inc.startswith("—") or sub.startswith("—"):
            raise ValueError("Please select incident medium and substrate.")
        layers = []
        for r in range(self.layer_table.rowCount()):
            item = self.layer_table.item(r, 0)
            page = item.data(Qt.ItemDataRole.UserRole)
            mat = self.db.get(item.text(), page=page)
            d = float(self.layer_table.item(r, 1).text())
            layers.append(Layer(mat, d))
        return Structure(layers=layers,
                         incident=self.db.get(inc),
                         substrate=self.db.get(sub),
                         substrate_coherent=False)

    def build_structure_opt(self, opt_idx, thicknesses):
        inc = self.combo_inc.currentText()
        sub = self.combo_sub.currentText()
        if inc.startswith("—"): inc = "Air"
        if sub.startswith("—"): sub = "Glass_BK7"
        layers = []; it = iter(thicknesses)
        for r in range(self.layer_table.rowCount()):
            item = self.layer_table.item(r, 0)
            page = item.data(Qt.ItemDataRole.UserRole)
            mat = self.db.get(item.text(), page=page)
            d = next(it) if r in opt_idx else float(self.layer_table.item(r, 1).text())
            layers.append(Layer(mat, d))
        return Structure(layers=layers,
                         incident=self.db.get(inc),
                         substrate=self.db.get(sub),
                         substrate_coherent=False)

    def get_conditions(self, fallback_wl_min=380, fallback_wl_max=800):
        conds = []
        for row in range(self.cond_table.rowCount()):
            try:
                conds.append((
                    float(self.cond_table.item(row, 0).text()),
                    float(self.cond_table.item(row, 1).text()),
                    self.cond_table.item(row, 2).text(),
                    self.cond_table.item(row, 3).text(),
                    float(self.cond_table.item(row, 4).text()),
                ))
            except (ValueError, AttributeError):
                pass
        if not conds:
            conds = [(fallback_wl_min, fallback_wl_max, "T", "max", 1.0)]
        return conds
