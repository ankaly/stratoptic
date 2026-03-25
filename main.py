"""
Stratoptic - Main Window (v1.0)
========================================================
Author      : Necmeddin
Institution : Gazi University, Department of Photonics
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QComboBox, QDoubleSpinBox,
    QSpinBox, QFrame, QSizePolicy, QCheckBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QFileDialog, QMessageBox, QInputDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QActionGroup

sys.path.insert(0, 'motor')
from rii_db import RIIDatabase
from engine import Layer, Structure, TMMEngine

from ui.theme import DARK, LIGHT, build_style, is_dark, sec, muted, hdiv, vdiv
from ui.canvases import SpectrumCanvas, DispersionCanvas, StackCanvas
from optimizer import OptimizeWorker

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


# =============================================================================
# OPTIMIZER
# =============================================================================

# =============================================================================
# MAIN WINDOW
# =============================================================================

class StratopticWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.db = RIIDatabase("data/rii_db")
        self._last_result = self._last_structure = None
        self._t = DARK if is_dark() else LIGHT
        self._worker = None

        self.setWindowTitle("Stratoptic")
        self.setMinimumSize(1100, 680)
        self.resize(1500, 900)
        self.setStyleSheet(build_style(self._t))
        self._build_menu()
        self._build_ui()
        self.statusBar().showMessage(
            "Stratoptic v1.0  ·  Licensed for: Gazi University Photonics Research Center")

    # ── Theme ──────────────────────────────────────────────────────────

    def _set_theme(self, mode):
        self._t = (DARK if (mode == "dark" or (mode == "auto" and is_dark()))
                   else LIGHT)
        self.setStyleSheet(build_style(self._t))
        self.canvas.apply_theme(self._t)
        self.stack_canvas.apply_theme(self._t)
        self.disp_canvas.apply_theme(self._t)

    # ── Menu ───────────────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("File")
        for txt, sc, fn in [
            ("Export Spectrum (PNG)…", "Ctrl+E", self._export_png),
            ("Export Data (CSV)…",     None,     self._export_csv),
        ]:
            a = QAction(txt, self)
            if sc: a.setShortcut(sc)
            a.triggered.connect(fn); fm.addAction(a)
        fm.addSeparator()
        imp = QAction("Import Material Dataset…", self); imp.setShortcut("Ctrl+I")
        imp.triggered.connect(self._import_dataset); fm.addAction(imp)
        fm.addSeparator()
        q = QAction("Quit", self); q.setShortcut("Ctrl+Q")
        q.triggered.connect(self.close); fm.addAction(q)

        vm = mb.addMenu("View")
        tm = vm.addMenu("Theme")
        grp = QActionGroup(self); grp.setExclusive(True)
        for mode, label in [("auto","Auto"),("dark","Dark"),("light","Light")]:
            a = QAction(label, self, checkable=True)
            a.setChecked(mode == "auto")
            a.triggered.connect(lambda c, m=mode: self._set_theme(m))
            grp.addAction(a); tm.addAction(a)

        tom = mb.addMenu("Tools")
        adb = QAction("Material Database…", self)
        adb.triggered.connect(self._show_db); tom.addAction(adb)

        hm = mb.addMenu("Help")
        ab = QAction("About Stratoptic", self)
        ab.triggered.connect(self._show_about); hm.addAction(ab)

    # ── UI skeleton ────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget(); root.setObjectName("root")
        self.setCentralWidget(root)
        vl = QVBoxLayout(root)
        vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(0)

        vl.addWidget(self._build_ribbon())
        vl.addWidget(self._build_sumbar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        sidebar = self._build_sidebar()
        splitter.addWidget(sidebar)
        splitter.addWidget(self._build_plotarea())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 1200])
        splitter.setHandleWidth(2)
        vl.addWidget(splitter)

    # ── Ribbon ─────────────────────────────────────────────────────────

    def _build_ribbon(self):
        ribbon = QWidget(); ribbon.setObjectName("ribbon")
        ribbon.setFixedHeight(92)
        hl = QHBoxLayout(ribbon)
        hl.setContentsMargins(16, 0, 12, 0); hl.setSpacing(0)

        # App identity
        id_w = QWidget()
        id_l = QVBoxLayout(id_w); id_l.setContentsMargins(0,0,0,0); id_l.setSpacing(1)
        id_l.addStretch()
        name = QLabel("STRATOPTIC"); name.setObjectName("appname")
        sub  = QLabel("Thin Film Simulation Platform"); sub.setObjectName("appsub")
        id_l.addWidget(name); id_l.addWidget(sub)
        id_l.addStretch()
        hl.addWidget(id_w)
        hl.addSpacing(16)
        hl.addWidget(vdiv(self._t))
        hl.addSpacing(14)

        # ── Calculation section ───────────────────────────────────────
        calc_w = QWidget()
        calc_l = QVBoxLayout(calc_w)
        calc_l.setContentsMargins(0, 8, 0, 4); calc_l.setSpacing(6)
        calc_l.addWidget(sec("Calculation"))

        r1 = QHBoxLayout(); r1.setSpacing(8)
        r1.addWidget(muted("λ range"))
        self.spin_wl_min = QSpinBox(); self.spin_wl_min.setRange(100, 5000)
        self.spin_wl_min.setValue(380); self.spin_wl_min.setSuffix(" nm")
        self.spin_wl_min.setFixedWidth(82)
        dash1 = muted("–"); dash1.setFixedWidth(8)
        dash1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_wl_max = QSpinBox(); self.spin_wl_max.setRange(100, 5000)
        self.spin_wl_max.setValue(800); self.spin_wl_max.setSuffix(" nm")
        self.spin_wl_max.setFixedWidth(82)
        r1.addWidget(self.spin_wl_min); r1.addWidget(dash1); r1.addWidget(self.spin_wl_max)
        r1.addSpacing(10)
        r1.addWidget(muted("pts"))
        self.spin_pts = QSpinBox(); self.spin_pts.setRange(50, 5000)
        self.spin_pts.setValue(500); self.spin_pts.setFixedWidth(68)
        r1.addWidget(self.spin_pts)
        calc_l.addLayout(r1)

        r2 = QHBoxLayout(); r2.setSpacing(8)
        r2.addWidget(muted("θ"))
        self.spin_angle = QDoubleSpinBox(); self.spin_angle.setRange(0, 89.9)
        self.spin_angle.setValue(0.0); self.spin_angle.setSuffix(" °")
        self.spin_angle.setSingleStep(1.0); self.spin_angle.setFixedWidth(70)
        r2.addWidget(self.spin_angle)
        r2.addSpacing(10)
        r2.addWidget(muted("pol"))
        self.combo_pol = QComboBox()
        self.combo_pol.addItems(["s (TE)", "p (TM)", "Unpolarized"])
        self.combo_pol.setFixedWidth(112)
        r2.addWidget(self.combo_pol)
        calc_l.addLayout(r2)

        hl.addWidget(calc_w)
        hl.addSpacing(10)
        hl.addWidget(vdiv(self._t))
        hl.addSpacing(14)

        # ── Optimization section ──────────────────────────────────────
        opt_w = QWidget()
        opt_l = QVBoxLayout(opt_w)
        opt_l.setContentsMargins(0, 8, 0, 4); opt_l.setSpacing(6)
        opt_l.addWidget(sec("Optimization"))

        ob = QHBoxLayout(); ob.setSpacing(8)
        ob.addWidget(muted("d bounds"))
        self.spin_d_min = QSpinBox(); self.spin_d_min.setRange(1, 10000)
        self.spin_d_min.setValue(1); self.spin_d_min.setSuffix(" nm")
        self.spin_d_min.setFixedWidth(74)
        dash2 = muted("–"); dash2.setFixedWidth(8)
        dash2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_d_max = QSpinBox(); self.spin_d_max.setRange(1, 10000)
        self.spin_d_max.setValue(500); self.spin_d_max.setSuffix(" nm")
        self.spin_d_max.setFixedWidth(74)
        ob.addWidget(self.spin_d_min); ob.addWidget(dash2); ob.addWidget(self.spin_d_max)
        opt_l.addLayout(ob)

        self.btn_opt = QPushButton("⚙  Optimize")
        self.btn_opt.setObjectName("warn")
        self.btn_opt.setFixedHeight(30)
        self.btn_opt.clicked.connect(self._run_optimization)
        opt_hint = muted("Check 'Opt' column in layer table")
        opt_l.addWidget(opt_hint)
        opt_l.addWidget(self.btn_opt)

        hl.addWidget(opt_w)
        hl.addSpacing(10)
        hl.addWidget(vdiv(self._t))
        hl.addSpacing(12)

        # ── Show + Calculate ──────────────────────────────────────────
        right_w = QWidget()
        right_l = QVBoxLayout(right_w)
        right_l.setContentsMargins(0, 8, 0, 4); right_l.setSpacing(8)
        right_l.addStretch()

        show_r = QHBoxLayout(); show_r.setSpacing(8)
        show_r.addWidget(muted("Show:"))
        self.chk_R = QCheckBox("R"); self.chk_R.setChecked(True)
        self.chk_T = QCheckBox("T"); self.chk_T.setChecked(True)
        self.chk_A = QCheckBox("A"); self.chk_A.setChecked(True)
        # Colored indicators
        self.chk_R.setStyleSheet(
            "QCheckBox{color:#FF453A;font-weight:700;spacing:5px;}"
            "QCheckBox::indicator{background:#FF453A25;border:1.5px solid #FF453A88;border-radius:4px;width:14px;height:14px;}"
            "QCheckBox::indicator:hover{border-color:#FF453A;}"
            "QCheckBox::indicator:checked{background:#FF453A;border-color:#FF453A;}"
        )
        self.chk_T.setStyleSheet(
            "QCheckBox{color:#0A84FF;font-weight:700;spacing:5px;}"
            "QCheckBox::indicator{background:#0A84FF25;border:1.5px solid #0A84FF88;border-radius:4px;width:14px;height:14px;}"
            "QCheckBox::indicator:hover{border-color:#0A84FF;}"
            "QCheckBox::indicator:checked{background:#0A84FF;border-color:#0A84FF;}"
        )
        self.chk_A.setStyleSheet(
            "QCheckBox{color:#32D74B;font-weight:700;spacing:5px;}"
            "QCheckBox::indicator{background:#32D74B25;border:1.5px solid #32D74B88;border-radius:4px;width:14px;height:14px;}"
            "QCheckBox::indicator:hover{border-color:#32D74B;}"
            "QCheckBox::indicator:checked{background:#32D74B;border-color:#32D74B;}"
        )
        for chk in [self.chk_R, self.chk_T, self.chk_A]:
            chk.stateChanged.connect(self._replot)
            show_r.addWidget(chk)
        right_l.addLayout(show_r)

        self.btn_calc = QPushButton("Calculate")
        self.btn_calc.setObjectName("calc")
        self.btn_calc.clicked.connect(self._calculate)
        right_l.addWidget(self.btn_calc)
        right_l.addStretch()
        hl.addWidget(right_w)

        return ribbon

    # ── Summary bar ────────────────────────────────────────────────────

    def _build_sumbar(self):
        w = QWidget(); w.setObjectName("sumbar"); w.setFixedHeight(44)
        hl = QHBoxLayout(w); hl.setContentsMargins(20, 0, 20, 0); hl.setSpacing(0)
        self._sw = {}
        for key, label, color in [
            ("R", "avg Reflectance",   "#FF453A"),
            ("T", "avg Transmittance", "#0A84FF"),
            ("A", "avg Absorbance",    "#32D74B"),
        ]:
            cell = QWidget()
            cl = QHBoxLayout(cell); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(8)
            val = QLabel("—"); val.setObjectName("statval")
            val.setStyleSheet(f"color:{color};font-size:15px;font-weight:700;")
            kl  = QLabel(label); kl.setObjectName("statkey")
            cl.addWidget(val); cl.addWidget(kl)
            self._sw[key] = val; hl.addWidget(cell)
            if key != "A":
                sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(
                    f"background:{self._t['line0']};max-width:1px;border:none;")
                hl.addSpacing(18); hl.addWidget(sep); hl.addSpacing(18)
        hl.addStretch()
        self.lbl_info = QLabel(""); self.lbl_info.setObjectName("statkey")
        self.lbl_info.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hl.addWidget(self.lbl_info)
        return w

    # ── Sidebar ────────────────────────────────────────────────────────

    def _build_sidebar(self):
        outer = QWidget(); outer.setObjectName("sidebar")
        outer.setMinimumWidth(240)
        outer.setSizePolicy(QSizePolicy.Policy.Preferred,
                            QSizePolicy.Policy.Expanding)
        ol = QVBoxLayout(outer); ol.setContentsMargins(0, 0, 0, 0); ol.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        il = QVBoxLayout(inner); il.setContentsMargins(14, 14, 14, 14); il.setSpacing(14)

        # ── Incident ──────────────────────────────────────────────────
        il.addWidget(sec("Incident Medium"))
        self.combo_inc = QComboBox()
        self.combo_inc.addItem("— Select incident medium —")
        inc_fixed = ["Air","Vacuum","SiO2","MgF2","Al2O3","CaF2","Glass_BK7"]
        for m in inc_fixed: self.combo_inc.addItem(m)
        for key, mats in sorted(self.db._index.items()):
            try:
                N = mats[0].N_at(550); name = mats[0].name
                if N.imag < 0.001 and 1.0 < N.real < 2.0 and name not in inc_fixed:
                    self.combo_inc.addItem(name)
            except: pass
        il.addWidget(self.combo_inc)
        il.addWidget(hdiv(self._t))

        # ── Layers ────────────────────────────────────────────────────
        il.addWidget(sec("Layers"))

        # Add row — all same height, properly aligned
        add_r = QHBoxLayout(); add_r.setSpacing(6)
        self.combo_mat = QComboBox()
        self.combo_mat.addItem("— Select material —")
        priority = ["TiO2","SiO2","Ag","Au","Al","Cr","MgF2","Al2O3",
                    "HfO2","Ta2O5","ZnO","Si3N4","Cu","Pt"]
        mats_list = [p for p in priority if p.lower() in self.db._index]
        for key in sorted(self.db._index.keys()):
            name = self.db._index[key][0].name
            if name not in mats_list and key not in ("air","vacuum"):
                mats_list.append(name)
        for m in mats_list: self.combo_mat.addItem(m)
        self.combo_mat.currentTextChanged.connect(self._update_dispersion)

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
        # Fixed columns for Opt and remove button
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
        # Row height
        self.layer_table.verticalHeader().setDefaultSectionSize(28)
        self.layer_table.cellChanged.connect(self._on_layer_edited)
        il.addWidget(self.layer_table)
        il.addWidget(hdiv(self._t))

        # ── Substrate ─────────────────────────────────────────────────
        il.addWidget(sec("Substrate"))
        self.combo_sub = QComboBox()
        self.combo_sub.addItem("— Select substrate —")
        sub_fixed = ["Glass_BK7","SiO2","Al2O3","CaF2","MgF2"]
        for m in sub_fixed: self.combo_sub.addItem(m)
        for key, ml in sorted(self.db._index.items()):
            try:
                N = ml[0].N_at(550); name = ml[0].name
                if N.imag < 0.01 and N.real > 1.0 and name not in sub_fixed:
                    self.combo_sub.addItem(name)
            except: pass
        il.addWidget(self.combo_sub)
        il.addWidget(hdiv(self._t))

        # ── Optimization Conditions ───────────────────────────────────
        il.addWidget(sec("Optimization Conditions"))

        # Conditions table — 6 columns, fixed widths that actually fit
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

        # Add condition row 1: λ range
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

        # Add condition row 2: metric / goal / weight / add button
        cr2 = QHBoxLayout(); cr2.setSpacing(6)
        self.combo_cm = QComboBox(); self.combo_cm.addItems(["R","T","A"])
        self.combo_cm.setFixedWidth(54)
        self.combo_cg = QComboBox(); self.combo_cg.addItems(["max","min"])
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
        return outer

    # ── Plot area ──────────────────────────────────────────────────────

    def _build_plotarea(self):
        w = QWidget(); w.setObjectName("plotarea")
        vl = QVBoxLayout(w); vl.setContentsMargins(8, 4, 8, 4); vl.setSpacing(4)

        vsplit = QSplitter(Qt.Orientation.Vertical)
        vsplit.setChildrenCollapsible(False)

        # Spectrum + toolbar
        self.canvas = SpectrumCanvas(self._t)
        nav = NavigationToolbar(self.canvas, w)
        # Remove subplot/customize buttons
        for action in nav.actions():
            if action.text() in ("Subplots", "Customize"):
                nav.removeAction(action)
        spec_w = QWidget()
        sl = QVBoxLayout(spec_w); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(0)
        sl.addWidget(self.canvas)
        sl.addWidget(nav)
        vsplit.addWidget(spec_w)

        # Bottom tabs — expanding tabs so names are fully visible
        self.btabs = QTabWidget()
        self.btabs.setDocumentMode(True)
        self.btabs.tabBar().setExpanding(True)

        self.stack_canvas = StackCanvas(self._t)
        self.btabs.addTab(self.stack_canvas, "Layer Stack")

        res_w = QTableWidget(0, 4)
        res_w.setHorizontalHeaderLabels(["λ (nm)","R (%)","T (%)","A (%)"])
        res_w.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        res_w.setAlternatingRowColors(True)
        res_w.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.res_table = res_w
        self.btabs.addTab(res_w, "Spectral Data")

        self.disp_canvas = DispersionCanvas(self._t)
        self.btabs.addTab(self.disp_canvas, "Dispersion")

        vsplit.addWidget(self.btabs)
        vsplit.setSizes([540, 200])
        vl.addWidget(vsplit)
        return w

    # ── Layer management ───────────────────────────────────────────────

    def _add_layer(self):
        mat = self.combo_mat.currentText()
        if mat.startswith("—"):
            self.statusBar().showMessage("Please select a material first."); return
        d = self.spin_d.value()
        row = self.layer_table.rowCount(); self.layer_table.insertRow(row)
        mat_item = QTableWidgetItem(mat)
        mat_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.layer_table.setItem(row, 0, mat_item)
        self.layer_table.setItem(row, 1, QTableWidgetItem(f"{d:.1f}"))
        # Opt checkbox — centered
        cw = QWidget(); cl = QHBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0); cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chk = QCheckBox(); cl.addWidget(chk)
        self.layer_table.setCellWidget(row, 2, cw)
        # Remove button — fits in row
        btn = QPushButton("✕"); btn.setObjectName("rm")
        btn.setFixedSize(26, 22); btn.clicked.connect(self._remove_layer)
        self.layer_table.setCellWidget(row, 3, btn)
        self._refresh_stack()
        self.statusBar().showMessage(f"Added: {mat}  {d:.1f} nm")

    def _remove_layer(self):
        btn = self.sender()
        for row in range(self.layer_table.rowCount()):
            if self.layer_table.cellWidget(row, 3) is btn:
                self.layer_table.removeRow(row); break
        self._refresh_stack()

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
        self._refresh_stack()

    def _swap_rows(self, r1, r2):
        t = self.layer_table
        t.blockSignals(True)
        mat1 = t.item(r1, 0).text(); d1 = t.item(r1, 1).text()
        opt1 = (w := t.cellWidget(r1, 2)) and (c := w.findChild(QCheckBox)) and c.isChecked()
        mat2 = t.item(r2, 0).text(); d2 = t.item(r2, 1).text()
        opt2 = (w := t.cellWidget(r2, 2)) and (c := w.findChild(QCheckBox)) and c.isChecked()

        for row, mat, d, opt in [(r1, mat2, d2, opt2), (r2, mat1, d1, opt1)]:
            mi = QTableWidgetItem(mat)
            mi.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
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
        self._refresh_stack()

    def _move_layer_down(self):
        row = self.layer_table.currentRow()
        if row < 0 or row >= self.layer_table.rowCount() - 1:
            return
        self._swap_rows(row, row + 1)
        self.layer_table.setCurrentCell(row + 1, 1)
        self._refresh_stack()

    def _get_opt_idx(self):
        return [r for r in range(self.layer_table.rowCount())
                if (w := self.layer_table.cellWidget(r, 2)) and
                   (c := w.findChild(QCheckBox)) and c.isChecked()]

    def _build_structure(self):
        inc = self.combo_inc.currentText()
        sub = self.combo_sub.currentText()
        if inc.startswith("—") or sub.startswith("—"):
            raise ValueError("Please select incident medium and substrate.")
        layers = []
        for r in range(self.layer_table.rowCount()):
            mat = self.db.get(self.layer_table.item(r, 0).text())
            d   = float(self.layer_table.item(r, 1).text())
            layers.append(Layer(mat, d))
        return Structure(layers=layers,
                         incident=self.db.get(inc),
                         substrate=self.db.get(sub),
                         substrate_coherent=False)

    def _build_structure_opt(self, opt_idx, thicknesses):
        inc = self.combo_inc.currentText()
        sub = self.combo_sub.currentText()
        if inc.startswith("—"): inc = "Air"
        if sub.startswith("—"): sub = "Glass_BK7"
        layers = []; it = iter(thicknesses)
        for r in range(self.layer_table.rowCount()):
            mat = self.db.get(self.layer_table.item(r, 0).text())
            d   = next(it) if r in opt_idx else float(self.layer_table.item(r, 1).text())
            layers.append(Layer(mat, d))
        return Structure(layers=layers,
                         incident=self.db.get(inc),
                         substrate=self.db.get(sub),
                         substrate_coherent=False)

    def _refresh_stack(self):
        try: self.stack_canvas.plot(self._build_structure(), self.db)
        except: self.stack_canvas._empty()

    def _update_dispersion(self, mat_name):
        if mat_name.startswith("—"): return
        try:
            mat = self.db.get(mat_name)
            self.disp_canvas.plot(mat, self.db)
            self.btabs.setCurrentWidget(self.disp_canvas)
        except: pass

    # ── Conditions ────────────────────────────────────────────────────

    def _add_cond(self):
        wl0 = self.spin_cwl0.value(); wl1 = self.spin_cwl1.value()
        if wl0 >= wl1:
            self.statusBar().showMessage("λ min must be < λ max"); return
        row = self.cond_table.rowCount(); self.cond_table.insertRow(row)
        self.cond_table.setItem(row, 0, QTableWidgetItem(str(wl0)))
        self.cond_table.setItem(row, 1, QTableWidgetItem(str(wl1)))
        self.cond_table.setItem(row, 2, QTableWidgetItem(self.combo_cm.currentText()))
        self.cond_table.setItem(row, 3, QTableWidgetItem(self.combo_cg.currentText()))
        self.cond_table.setItem(row, 4, QTableWidgetItem(f"{self.spin_cw.value():.2f}"))
        btn = QPushButton("✕"); btn.setObjectName("rm")
        btn.setFixedSize(22, 20); btn.clicked.connect(self._remove_cond)
        self.cond_table.setCellWidget(row, 5, btn)

    def _remove_cond(self):
        btn = self.sender()
        for row in range(self.cond_table.rowCount()):
            if self.cond_table.cellWidget(row, 5) is btn:
                self.cond_table.removeRow(row); break

    def _get_conditions(self):
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
            except: pass
        if not conds:
            conds = [(self.spin_wl_min.value(), self.spin_wl_max.value(),
                      "T", "max", 1.0)]
        return conds

    # ── Calculation ────────────────────────────────────────────────────

    def _get_pol(self):
        t = self.combo_pol.currentText()
        if "s" in t: return "s"
        if "p" in t: return "p"
        return "unpolarized"

    def _calculate(self):
        try:
            st = self._build_structure()
            wl = np.linspace(self.spin_wl_min.value(),
                             self.spin_wl_max.value(),
                             self.spin_pts.value())
            pol = self._get_pol(); ang = self.spin_angle.value()
            result = TMMEngine(st).calculate(wl, angle=ang,
                                              polarization=pol,
                                              substrate_thickness_mm=1.0)
            self._last_result = result; self._last_structure = st
            self.canvas.plot(result, self.chk_R.isChecked(),
                             self.chk_T.isChecked(), self.chk_A.isChecked(), st)
            self._sw["R"].setText(f"{result.R.mean()*100:.2f}%")
            self._sw["T"].setText(f"{result.T.mean()*100:.2f}%")
            self._sw["A"].setText(f"{result.A.mean()*100:.2f}%")
            self.lbl_info.setText(
                f"λ {wl[0]:.0f}–{wl[-1]:.0f} nm  ·  {len(wl)} pts  ·  {pol}  ·  θ={ang}°")
            step = max(1, len(wl)//50)
            self.res_table.setRowCount(0)
            for i in range(0, len(wl), step):
                r = self.res_table.rowCount(); self.res_table.insertRow(r)
                self.res_table.setItem(r, 0, QTableWidgetItem(f"{wl[i]:.1f}"))
                self.res_table.setItem(r, 1, QTableWidgetItem(f"{result.R[i]*100:.3f}"))
                self.res_table.setItem(r, 2, QTableWidgetItem(f"{result.T[i]*100:.3f}"))
                self.res_table.setItem(r, 3, QTableWidgetItem(f"{result.A[i]*100:.3f}"))
                self.res_table.item(r, 1).setForeground(QColor("#FF453A"))
                self.res_table.item(r, 2).setForeground(QColor("#0A84FF"))
                self.res_table.item(r, 3).setForeground(QColor("#32D74B"))
            self.stack_canvas.plot(st, self.db)
            self.btabs.setCurrentIndex(0)
            self.statusBar().showMessage("Calculation complete.")
        except Exception as e:
            import traceback
            self.statusBar().showMessage(f"Error: {e}")
            print(traceback.format_exc())

    def _replot(self):
        if self._last_result:
            self.canvas.plot(self._last_result, self.chk_R.isChecked(),
                             self.chk_T.isChecked(), self.chk_A.isChecked(),
                             self._last_structure)

    # ── Optimization ───────────────────────────────────────────────────

    def _run_optimization(self):
        oi = self._get_opt_idx()
        if not oi:
            self.statusBar().showMessage("No layers selected for optimization."); return
        conds  = self._get_conditions()
        bounds = [(self.spin_d_min.value(), self.spin_d_max.value())] * len(oi)
        self.btn_opt.setEnabled(False)
        cs = "  ·  ".join([f"{m} {g} [{w0:.0f}–{w1:.0f}nm]×{wt}"
                            for w0,w1,m,g,wt in conds])
        self.statusBar().showMessage(f"Optimizing {len(oi)} layer(s)  ·  {cs}")
        self._worker = OptimizeWorker(
            self._build_structure_opt, oi, bounds, conds,
            self._get_pol(), self.spin_angle.value())
        self._worker.progress.connect(self.statusBar().showMessage)
        self._worker.finished.connect(self._on_opt_done)
        self._worker.start()

    def _on_opt_done(self, thicknesses, obj_val):
        self.btn_opt.setEnabled(True)
        for i, row in enumerate(self._get_opt_idx()):
            self.layer_table.setItem(row, 1, QTableWidgetItem(f"{thicknesses[i]:.1f}"))
        self.statusBar().showMessage(
            f"Done  ·  obj={obj_val:.4f}  ·  " +
            "  ".join([f"L{i+1}={d:.1f}nm" for i,d in enumerate(thicknesses)]))
        self._calculate()

    # ── Export ─────────────────────────────────────────────────────────

    def _export_png(self):
        if not self._last_result: return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export", "spectrum.png", "PNG (*.png);;PDF (*.pdf)")
        if path: self.canvas.save(path)

    def _export_csv(self):
        if not self._last_result: return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "spectrum.csv", "CSV (*.csv)")
        if path:
            r = self._last_result
            np.savetxt(path, np.column_stack([r.wavelengths, r.R, r.T, r.A]),
                       delimiter=",", header="wavelength_nm,R,T,A", comments="")

    def _import_dataset(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Material Dataset", "",
            "CSV/TXT (*.csv *.txt *.dat);;All files (*)")
        if not path:
            return
        name, ok = QInputDialog.getText(self, "Material Name",
                                        "Enter a name for this material:")
        if not ok or not name.strip():
            return
        name = name.strip()
        try:
            mat = self.db.load_user_dataset(path, name)
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", str(e)); return

        wl0, wl1 = mat._wl_range
        try:
            n_pts = len(mat._interp_n.x)
        except Exception:
            n_pts = 0

        for combo in [self.combo_mat, self.combo_inc, self.combo_sub]:
            combo.addItem(name)

        self.statusBar().showMessage(
            f"Loaded: {name}  ({n_pts} points, {wl0:.0f}–{wl1:.0f} nm)")

    # ── Dialogs ────────────────────────────────────────────────────────

    def _show_db(self):
        lines = [f"{mats[0].name:<18} n@550={mats[0].n_ref:.4f}  k@550={mats[0].k_ref:.4f}"
                 for mats in list(self.db._index.values())[:50]]
        QMessageBox.information(self, "Material Database", "\n".join(lines))

    def _show_about(self):
        QMessageBox.about(self, "About Stratoptic",
            "Stratoptic v1.0\n\nThin Film Design & Simulation Platform\n"
            "Byrnes (2021) TMM + RefractiveIndex.info DB\n\n"
            "Author: Necmeddin\n"
            "Gazi University Photonics Research Center\n\n"
            "Byrnes, arXiv:1603.02720 (2021)\n"
            "Johnson & Christy, Phys. Rev. B 6 (1972)\n"
            "Born & Wolf, Principles of Optics (1999)")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Stratoptic")
    window = StratopticWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
