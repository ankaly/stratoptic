"""
Stratoptic - Main Window (v0.3)
========================================================
Author      : Necmeddin
Institution : Gazi University, Department of Photonics
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QComboBox, QDoubleSpinBox,
    QSpinBox, QGroupBox, QFrame, QSizePolicy, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QStatusBar,
    QMenuBar, QMenu, QToolBar, QTabWidget, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QAction, QIcon, QColor

sys.path.insert(0, 'motor')
from rii_db import RIIDatabase
from engine import Layer, Structure, TMMEngine

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches


# =============================================================================
# STYLE
# =============================================================================

STYLE = """
* {
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    font-size: 12px;
}
QMainWindow { background-color: #1C1C1E; }
QWidget#central { background-color: #1C1C1E; }
QWidget#left_panel {
    background-color: #2C2C2E;
    border-right: 1px solid #3A3A3C;
}
QWidget#right_panel { background-color: #1C1C1E; }
QGroupBox {
    background-color: #2C2C2E;
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    color: #EBEBF5;
    font-weight: 600;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px; top: -1px;
    padding: 0 6px;
    color: #0A84FF;
    background-color: #2C2C2E;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QPushButton {
    background-color: #0A84FF;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
    min-height: 30px;
}
QPushButton:hover { background-color: #409CFF; }
QPushButton:pressed { background-color: #0060D0; }
QPushButton#btn_add {
    background-color: #3A3A3C;
    color: #EBEBF5;
    border: 1px solid #4A4A4C;
}
QPushButton#btn_add:hover { background-color: #48484A; }
QPushButton#btn_remove {
    background-color: transparent;
    color: #FF453A;
    border: 1px solid #FF453A;
    padding: 3px 8px;
    min-height: 22px;
    font-size: 11px;
}
QPushButton#btn_remove:hover { background-color: #3A1A1A; }
QComboBox, QDoubleSpinBox, QSpinBox {
    background-color: #3A3A3C;
    color: #EBEBF5;
    border: 1px solid #48484A;
    border-radius: 5px;
    padding: 4px 8px;
    min-height: 26px;
}
QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #0A84FF;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #3A3A3C;
    color: #EBEBF5;
    selection-background-color: #0A84FF;
    border: 1px solid #48484A;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #48484A; border: none; width: 16px;
}
QTableWidget {
    background-color: #2C2C2E;
    color: #EBEBF5;
    gridline-color: #3A3A3C;
    border: 1px solid #3A3A3C;
    border-radius: 6px;
    alternate-background-color: #323234;
}
QTableWidget::item:selected {
    background-color: #0A84FF30;
    color: #EBEBF5;
}
QHeaderView::section {
    background-color: #3A3A3C;
    color: #8E8E93;
    border: none;
    border-bottom: 1px solid #48484A;
    padding: 6px 8px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
}
QTabWidget::pane {
    border: 1px solid #3A3A3C;
    border-radius: 0 6px 6px 6px;
    background-color: #2C2C2E;
}
QTabBar::tab {
    background-color: #3A3A3C;
    color: #8E8E93;
    border: none;
    padding: 7px 16px;
    font-size: 11px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #2C2C2E;
    color: #0A84FF;
    border-bottom: 2px solid #0A84FF;
}
QTabBar::tab:hover { color: #EBEBF5; }
QCheckBox { color: #EBEBF5; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px;
    border-radius: 3px;
    border: 1px solid #48484A;
    background-color: #3A3A3C;
}
QCheckBox::indicator:checked {
    background-color: #0A84FF;
    border-color: #0A84FF;
}
QLabel { color: #EBEBF5; }
QLabel#label_app_name {
    color: #EBEBF5; font-size: 18px; font-weight: 700;
}
QLabel#label_app_sub { color: #8E8E93; font-size: 11px; }
QLabel#label_section {
    color: #8E8E93; font-size: 10px;
    font-weight: 600; letter-spacing: 1px;
}
QSplitter::handle { background-color: #3A3A3C; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
QMenuBar {
    background-color: #2C2C2E;
    color: #EBEBF5;
    border-bottom: 1px solid #3A3A3C;
    padding: 2px;
}
QMenuBar::item:selected { background-color: #3A3A3C; border-radius: 4px; }
QMenu {
    background-color: #2C2C2E;
    color: #EBEBF5;
    border: 1px solid #3A3A3C;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item { padding: 6px 20px; border-radius: 4px; }
QMenu::item:selected { background-color: #0A84FF; }
QMenu::separator { height: 1px; background-color: #3A3A3C; margin: 4px 0; }
QToolBar {
    background-color: #2C2C2E;
    border-bottom: 1px solid #3A3A3C;
    padding: 4px 8px; spacing: 4px;
}
QStatusBar {
    background-color: #2C2C2E;
    color: #8E8E93;
    border-top: 1px solid #3A3A3C;
    font-size: 11px; padding: 2px 8px;
}
QScrollBar:vertical {
    background: #2C2C2E; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #48484A; border-radius: 4px; min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


# =============================================================================
# SPECTRUM CANVAS
# =============================================================================

class SpectrumCanvas(FigureCanvas):

    BG      = "#1C1C1E"
    AX_BG   = "#2C2C2E"
    GRID    = "#3A3A3C"
    TEXT    = "#EBEBF5"
    MUTED   = "#8E8E93"
    COLOR_R = "#FF453A"
    COLOR_T = "#0A84FF"
    COLOR_A = "#30D158"

    def __init__(self, parent=None):
        self.fig = Figure(facecolor=self.BG)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._result = None
        self._init_axes()

    def _init_axes(self):
        self.fig.clear()
        gs = gridspec.GridSpec(1, 1, figure=self.fig,
                               left=0.08, right=0.97, top=0.93, bottom=0.12)
        self.ax = self.fig.add_subplot(gs[0], facecolor=self.AX_BG)
        self._style_ax(self.ax)
        self.ax.text(0.5, 0.5, "Add layers and click Calculate",
                     transform=self.ax.transAxes,
                     ha="center", va="center",
                     color=self.MUTED, fontsize=13)
        self.draw()

    def _style_ax(self, ax):
        ax.tick_params(colors=self.MUTED, labelsize=9, length=3)
        ax.set_xlabel("Wavelength (nm)", color=self.MUTED, fontsize=10, labelpad=6)
        ax.set_ylabel("Intensity (%)", color=self.MUTED, fontsize=10, labelpad=6)
        ax.set_xlim(380, 800)
        ax.set_ylim(-2, 102)
        ax.grid(True, color=self.GRID, alpha=0.8, linewidth=0.6)
        ax.grid(True, which="minor", color=self.GRID, alpha=0.3, linewidth=0.4)
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        for spine in ax.spines.values():
            spine.set_edgecolor(self.GRID)
            spine.set_linewidth(0.8)

    def plot(self, result, show_R=True, show_T=True, show_A=True, structure=None):
        self._result = result
        self.fig.clear()
        gs = gridspec.GridSpec(1, 1, figure=self.fig,
                               left=0.08, right=0.97, top=0.90, bottom=0.12)
        ax = self.fig.add_subplot(gs[0], facecolor=self.AX_BG)
        self._style_ax(ax)
        self.ax = ax

        wl = result.wavelengths
        if show_R:
            ax.plot(wl, result.R * 100, color=self.COLOR_R, lw=1.8,
                    label="Reflectance (R)", zorder=3)
            ax.fill_between(wl, result.R * 100, alpha=0.08,
                            color=self.COLOR_R, zorder=2)
        if show_T:
            ax.plot(wl, result.T * 100, color=self.COLOR_T, lw=1.8,
                    label="Transmittance (T)", zorder=3)
            ax.fill_between(wl, result.T * 100, alpha=0.08,
                            color=self.COLOR_T, zorder=2)
        if show_A:
            ax.plot(wl, result.A * 100, color=self.COLOR_A, lw=1.8,
                    label="Absorbance (A)", zorder=3)
            ax.fill_between(wl, result.A * 100, alpha=0.08,
                            color=self.COLOR_A, zorder=2)

        ax.legend(loc="upper right", fontsize=9,
                  facecolor="#3A3A3C", labelcolor=self.TEXT,
                  edgecolor=self.GRID, framealpha=0.9,
                  handlelength=1.5, handletextpad=0.5)
        ax.set_xlim(wl[0], wl[-1])
        ax.set_ylim(-2, 102)

        pol_str = result.polarization.upper()
        if structure:
            stack = " / ".join(
                [structure.incident.name] +
                [f"{l.material.name}({l.thickness:.0f}nm)" for l in structure.layers] +
                [structure.substrate.name]
            )
            title = f"{stack}   ·   pol: {pol_str}   ·   θ: {result.angle}°"
        else:
            title = f"TMM Spectrum   ·   pol: {pol_str}   ·   θ: {result.angle}°"

        self.fig.suptitle(title, color=self.MUTED, fontsize=9,
                          x=0.5, y=0.97, ha="center")
        self.draw()

    def save(self, path: str):
        self.fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=self.BG)


# =============================================================================
# STACK DIAGRAM CANVAS
# =============================================================================

class StackCanvas(FigureCanvas):

    BG    = "#1C1C1E"
    TEXT  = "#EBEBF5"
    MUTED = "#8E8E93"

    LAYER_COLORS = {
        "ambient":    "#1A2A3A",
        "dielectric": "#0A4A7A",
        "metal":      "#4A3A0A",
        "other":      "#3A3A4A",
        "substrate":  "#2A2A3A",
    }

    def __init__(self, parent=None):
        self.fig = Figure(facecolor=self.BG)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._draw_empty()

    def _draw_empty(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor=self.BG)
        ax.axis("off")
        ax.text(0.5, 0.5, "No layers defined",
                transform=ax.transAxes, ha="center", va="center",
                color=self.MUTED, fontsize=11)
        self.draw()

    def plot(self, structure, db):
        self.fig.clear()
        all_layers = (
            [("incident", structure.incident, None)] +
            [(f"L{i+1}", l.material, l.thickness)
             for i, l in enumerate(structure.layers)] +
            [("substrate", structure.substrate, None)]
        )
        n = len(all_layers)
        ax = self.fig.add_subplot(111, facecolor=self.BG)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, n + 0.5)
        ax.axis("off")

        for i, (role, mat, thick) in enumerate(reversed(all_layers)):
            y = i
            if role == "incident":
                color = self.LAYER_COLORS["ambient"]
            elif role == "substrate":
                color = self.LAYER_COLORS["substrate"]
            else:
                try:
                    k = mat.N_at(550).imag
                    color = (self.LAYER_COLORS["metal"] if k > 0.1
                             else self.LAYER_COLORS["dielectric"])
                except Exception:
                    color = self.LAYER_COLORS["other"]

            alpha = 0.9 if role not in ("incident", "substrate") else 0.5
            edge  = "#0A84FF" if role not in ("incident", "substrate") else "#3A3A3C"
            rect  = mpatches.FancyBboxPatch(
                (0.02, y + 0.05), 0.96, 0.87,
                boxstyle="round,pad=0.01",
                facecolor=color, edgecolor=edge,
                linewidth=1.0 if role not in ("incident","substrate") else 0.5,
                alpha=alpha, zorder=2
            )
            ax.add_patch(rect)

            n_val = mat.N_at(550).real
            if thick is not None:
                label = f"{mat.name}   ·   n={n_val:.3f}   ·   {thick:.0f} nm"
            else:
                tag = "incident" if role == "incident" else "substrate"
                label = f"{mat.name}   ·   n={n_val:.3f}   ({tag})"

            ax.text(0.5, y + 0.47, label,
                    ha="center", va="center",
                    color=self.TEXT, fontsize=9,
                    fontweight="600" if role not in ("incident","substrate") else "400",
                    zorder=3)

        ax.annotate("", xy=(0.5, n - 0.4), xytext=(0.5, n + 0.2),
                    arrowprops=dict(arrowstyle="-|>", color="#0A84FF", lw=1.5),
                    zorder=4)
        ax.text(0.5, n + 0.3, "Incident light",
                ha="center", va="bottom", color="#0A84FF",
                fontsize=9, fontweight="600")

        self.fig.tight_layout(pad=0.5)
        self.draw()


# =============================================================================
# RESULTS TABLE
# =============================================================================

class ResultsTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels(["λ (nm)", "R (%)", "T (%)", "A (%)"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def populate(self, result, step: int = 10):
        self.setRowCount(0)
        wl = result.wavelengths
        for i in range(0, len(wl), step):
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(f"{wl[i]:.1f}"))
            self.setItem(row, 1, QTableWidgetItem(f"{result.R[i]*100:.3f}"))
            self.setItem(row, 2, QTableWidgetItem(f"{result.T[i]*100:.3f}"))
            self.setItem(row, 3, QTableWidgetItem(f"{result.A[i]*100:.3f}"))
            self.item(row, 1).setForeground(QColor("#FF453A"))
            self.item(row, 2).setForeground(QColor("#0A84FF"))
            self.item(row, 3).setForeground(QColor("#30D158"))


# =============================================================================
# MAIN WINDOW
# =============================================================================

class StratopticWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.db = RIIDatabase("data/rii_db")
        self._last_result    = None
        self._last_structure = None

        self.setWindowTitle("Stratoptic")
        self.setMinimumSize(1300, 750)
        self.resize(1500, 860)
        self.setStyleSheet(STYLE)

        self._build_menu()
        self._build_toolbar()
        self._build_ui()
        self.statusBar().showMessage(
            "Stratoptic v0.3.0  ·  Gazi University Photonics  ·  Ready"
        )

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        act_png = QAction("Export Spectrum (PNG)...", self)
        act_png.setShortcut("Ctrl+E")
        act_png.triggered.connect(self._export_png)
        act_csv = QAction("Export Data (CSV)...", self)
        act_csv.triggered.connect(self._export_csv)
        act_quit = QAction("Quit", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_png)
        file_menu.addAction(act_csv)
        file_menu.addSeparator()
        file_menu.addAction(act_quit)

        tools_menu = mb.addMenu("Tools")
        act_db = QAction("Material Database...", self)
        act_db.triggered.connect(self._show_db)
        tools_menu.addAction(act_db)

        help_menu = mb.addMenu("Help")
        act_about = QAction("About Stratoptic", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        btn_calc = QPushButton("▶  Calculate")
        btn_calc.clicked.connect(self._calculate)
        btn_calc.setFixedHeight(28)
        tb.addWidget(btn_calc)
        tb.addSeparator()
        tb.addWidget(QLabel("  Show: "))

        self.chk_R = QCheckBox("R"); self.chk_R.setChecked(True)
        self.chk_T = QCheckBox("T"); self.chk_T.setChecked(True)
        self.chk_A = QCheckBox("A"); self.chk_A.setChecked(True)
        for chk in [self.chk_R, self.chk_T, self.chk_A]:
            chk.stateChanged.connect(self._replot)
            tb.addWidget(chk)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left())
        splitter.addWidget(self._build_right())
        splitter.setSizes([360, 1100])
        splitter.setHandleWidth(1)
        root.addWidget(splitter)

    def _build_left(self) -> QWidget:
        w = QWidget()
        w.setObjectName("left_panel")
        w.setMinimumWidth(300)
        w.setMaximumWidth(420)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        name_lbl = QLabel("STRATOPTIC")
        name_lbl.setObjectName("label_app_name")
        sub_lbl = QLabel("Thin Film Simulation Platform")
        sub_lbl.setObjectName("label_app_sub")
        layout.addWidget(name_lbl)
        layout.addWidget(sub_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3A3A3C;")
        layout.addWidget(sep)

        layout.addWidget(self._build_structure_group())
        layout.addWidget(self._build_settings_group())

        btn_calc = QPushButton("▶   Calculate Spectrum")
        btn_calc.setMinimumHeight(36)
        btn_calc.clicked.connect(self._calculate)
        layout.addWidget(btn_calc)
        layout.addStretch()
        return w

    def _build_structure_group(self) -> QGroupBox:
        g = QGroupBox("Structure")
        layout = QVBoxLayout(g)
        layout.setSpacing(6)

        # ── Incident ──────────────────────────────────────────────────
        row = QHBoxLayout()
        lbl = QLabel("Incident")
        lbl.setObjectName("label_section")
        lbl.setFixedWidth(65)
        row.addWidget(lbl)
        self.combo_incident = QComboBox()
        incident_fixed = ["Air", "Vacuum", "SiO2", "MgF2",
                          "Al2O3", "CaF2", "Glass_BK7"]
        for m in incident_fixed:
            self.combo_incident.addItem(m)
        for key, mats in sorted(self.db._index.items()):
            try:
                N = mats[0].N_at(550)
                name = mats[0].name
                if (N.imag < 0.001 and 1.0 < N.real < 2.0
                        and name not in incident_fixed):
                    self.combo_incident.addItem(name)
            except Exception:
                pass
        row.addWidget(self.combo_incident)
        layout.addLayout(row)

        # ── Layer table ───────────────────────────────────────────────
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Material", "d (nm)", ""])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 36)
        self.table.setMinimumHeight(150)
        self.table.setMaximumHeight(220)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # ── Add layer controls ────────────────────────────────────────
        add_row = QHBoxLayout()
        self.combo_mat = QComboBox()
        priority = ["TiO2", "SiO2", "Ag", "Au", "Al", "Cr",
                    "MgF2", "Al2O3", "HfO2", "Ta2O5", "ZnO",
                    "Si3N4", "Cu", "Pt"]
        mats = [p for p in priority if p.lower() in self.db._index]
        for key in sorted(self.db._index.keys()):
            name = self.db._index[key][0].name
            if name not in mats and key not in ("air", "vacuum"):
                mats.append(name)
        for m in mats:
            self.combo_mat.addItem(m)

        self.spin_d = QDoubleSpinBox()
        self.spin_d.setRange(0.1, 50000)
        self.spin_d.setValue(100.0)
        self.spin_d.setDecimals(1)
        self.spin_d.setSuffix(" nm")

        btn_add = QPushButton("+ Add")
        btn_add.setObjectName("btn_add")
        btn_add.setFixedWidth(60)
        btn_add.clicked.connect(self._add_layer)

        add_row.addWidget(self.combo_mat, 3)
        add_row.addWidget(self.spin_d, 2)
        add_row.addWidget(btn_add, 1)
        layout.addLayout(add_row)

        # ── Substrate ─────────────────────────────────────────────────
        row2 = QHBoxLayout()
        lbl2 = QLabel("Substrate")
        lbl2.setObjectName("label_section")
        lbl2.setFixedWidth(65)
        row2.addWidget(lbl2)
        self.combo_substrate = QComboBox()
        substrate_fixed = ["Glass_BK7", "SiO2", "Al2O3", "CaF2", "MgF2"]
        for m in substrate_fixed:
            self.combo_substrate.addItem(m)
        for key, mats_list in sorted(self.db._index.items()):
            try:
                N = mats_list[0].N_at(550)
                name = mats_list[0].name
                if (N.imag < 0.01 and N.real > 1.0
                        and name not in substrate_fixed):
                    self.combo_substrate.addItem(name)
            except Exception:
                pass
        row2.addWidget(self.combo_substrate)
        layout.addLayout(row2)

        return g

    def _build_settings_group(self) -> QGroupBox:
        g = QGroupBox("Calculation Settings")
        layout = QVBoxLayout(g)
        layout.setSpacing(6)

        def row_widget(label, widget):
            r = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setObjectName("label_section")
            lbl.setFixedWidth(80)
            r.addWidget(lbl)
            r.addWidget(widget)
            return r

        wl_row = QHBoxLayout()
        lbl_wl = QLabel("λ range")
        lbl_wl.setObjectName("label_section")
        lbl_wl.setFixedWidth(80)
        self.spin_wl_min = QSpinBox()
        self.spin_wl_min.setRange(100, 5000)
        self.spin_wl_min.setValue(380)
        self.spin_wl_min.setSuffix(" nm")
        dash = QLabel("–")
        dash.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash.setFixedWidth(12)
        self.spin_wl_max = QSpinBox()
        self.spin_wl_max.setRange(100, 5000)
        self.spin_wl_max.setValue(800)
        self.spin_wl_max.setSuffix(" nm")
        wl_row.addWidget(lbl_wl)
        wl_row.addWidget(self.spin_wl_min)
        wl_row.addWidget(dash)
        wl_row.addWidget(self.spin_wl_max)
        layout.addLayout(wl_row)

        self.spin_pts = QSpinBox()
        self.spin_pts.setRange(50, 5000)
        self.spin_pts.setValue(500)
        layout.addLayout(row_widget("Points", self.spin_pts))

        self.spin_angle = QDoubleSpinBox()
        self.spin_angle.setRange(0.0, 89.9)
        self.spin_angle.setValue(0.0)
        self.spin_angle.setSuffix(" °")
        self.spin_angle.setSingleStep(1.0)
        layout.addLayout(row_widget("Angle (θ)", self.spin_angle))

        self.combo_pol = QComboBox()
        self.combo_pol.addItems(["s (TE)", "p (TM)", "Unpolarized"])
        layout.addLayout(row_widget("Polarization", self.combo_pol))

        return g

    def _build_right(self) -> QWidget:
        w = QWidget()
        w.setObjectName("right_panel")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        layout.addWidget(self._build_summary_row())

        v_splitter = QSplitter(Qt.Orientation.Vertical)

        self.canvas = SpectrumCanvas()
        nav = NavigationToolbar(self.canvas, w)
        nav.setStyleSheet("background: #2C2C2E; color: #8E8E93;")
        spec_w = QWidget()
        spec_layout = QVBoxLayout(spec_w)
        spec_layout.setContentsMargins(0, 0, 0, 0)
        spec_layout.setSpacing(2)
        spec_layout.addWidget(self.canvas)
        spec_layout.addWidget(nav)
        v_splitter.addWidget(spec_w)

        tabs = QTabWidget()
        self.stack_canvas = StackCanvas()
        tabs.addTab(self.stack_canvas, "Layer Stack")
        self.results_table = ResultsTable()
        tabs.addTab(self.results_table, "Spectral Data")

        v_splitter.addWidget(tabs)
        v_splitter.setSizes([480, 220])
        v_splitter.setHandleWidth(1)
        layout.addWidget(v_splitter)
        return w

    def _build_summary_row(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #2C2C2E; border-radius: 6px;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(0)
        w.setFixedHeight(56)

        self._summary_widgets = {}
        for key, label, color in [
            ("R", "Reflectance",   "#FF453A"),
            ("T", "Transmittance", "#0A84FF"),
            ("A", "Absorbance",    "#30D158"),
        ]:
            cell = QWidget()
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(20, 4, 20, 4)
            cl.setSpacing(1)
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet(
                f"color: {color}; font-size: 16px; font-weight: 700;")
            key_lbl = QLabel(f"avg {label}")
            key_lbl.setObjectName("label_section")
            cl.addWidget(val_lbl)
            cl.addWidget(key_lbl)
            self._summary_widgets[key] = val_lbl
            layout.addWidget(cell)
            if key != "A":
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet("color: #3A3A3C;")
                layout.addWidget(sep)

        layout.addStretch()
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("color: #8E8E93; font-size: 10px;")
        self.lbl_info.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.lbl_info)
        return w

    # ------------------------------------------------------------------
    # Layer management
    # ------------------------------------------------------------------

    def _add_layer(self):
        mat = self.combo_mat.currentText()
        d   = self.spin_d.value()
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(mat))
        self.table.setItem(row, 1, QTableWidgetItem(f"{d:.1f}"))
        btn = QPushButton("✕")
        btn.setObjectName("btn_remove")
        btn.setFixedSize(30, 22)
        btn.clicked.connect(self._remove_current_layer)
        self.table.setCellWidget(row, 2, btn)
        self._update_stack_diagram()
        self.statusBar().showMessage(f"Added: {mat}  {d:.1f} nm")

    def _remove_current_layer(self):
        btn = self.sender()
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, 2) is btn:
                self.table.removeRow(row)
                break
        self._update_stack_diagram()

    def _build_structure(self) -> Structure:
        incident  = self.db.get(self.combo_incident.currentText())
        substrate = self.db.get(self.combo_substrate.currentText())
        layers = []
        for row in range(self.table.rowCount()):
            mat = self.db.get(self.table.item(row, 0).text())
            d   = float(self.table.item(row, 1).text())
            layers.append(Layer(mat, d))
        return Structure(layers=layers, incident=incident,
                         substrate=substrate, substrate_coherent=False)

    def _update_stack_diagram(self):
        try:
            structure = self._build_structure()
            self.stack_canvas.plot(structure, self.db)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Calculation
    # ------------------------------------------------------------------

    def _get_pol(self) -> str:
        t = self.combo_pol.currentText()
        if "s" in t:
            return "s"
        if "p" in t:
            return "p"
        return "unpolarized"

    def _calculate(self):
        try:
            structure = self._build_structure()
            wl = np.linspace(self.spin_wl_min.value(),
                             self.spin_wl_max.value(),
                             self.spin_pts.value())
            pol   = self._get_pol()
            angle = self.spin_angle.value()

            engine = TMMEngine(structure)
            result = engine.calculate(wl, angle=angle, polarization=pol,
                                      substrate_thickness_mm=1.0)

            self._last_result    = result
            self._last_structure = structure

            self.canvas.plot(result,
                             show_R=self.chk_R.isChecked(),
                             show_T=self.chk_T.isChecked(),
                             show_A=self.chk_A.isChecked(),
                             structure=structure)

            self._summary_widgets["R"].setText(f"{result.R.mean()*100:.2f}%")
            self._summary_widgets["T"].setText(f"{result.T.mean()*100:.2f}%")
            self._summary_widgets["A"].setText(f"{result.A.mean()*100:.2f}%")

            self.lbl_info.setText(
                f"λ: {wl[0]:.0f}–{wl[-1]:.0f} nm   ·   "
                f"{len(wl)} pts   ·   pol: {pol}   ·   θ: {angle}°"
            )

            step = max(1, len(wl) // 50)
            self.results_table.populate(result, step=step)
            self.stack_canvas.plot(structure, self.db)
            self.statusBar().showMessage("Calculation complete.")

        except Exception as e:
            import traceback
            self.statusBar().showMessage(f"Error: {e}")
            print(traceback.format_exc())

    def _replot(self):
        if self._last_result is None:
            return
        self.canvas.plot(self._last_result,
                         show_R=self.chk_R.isChecked(),
                         show_T=self.chk_T.isChecked(),
                         show_A=self.chk_A.isChecked(),
                         structure=self._last_structure)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_png(self):
        if self._last_result is None:
            self.statusBar().showMessage("No result to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Spectrum", "spectrum.png",
            "PNG Image (*.png);;PDF (*.pdf)")
        if path:
            self.canvas.save(path)
            self.statusBar().showMessage(f"Saved: {path}")

    def _export_csv(self):
        if self._last_result is None:
            self.statusBar().showMessage("No result to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "spectrum.csv", "CSV (*.csv)")
        if path:
            r = self._last_result
            data = np.column_stack([r.wavelengths, r.R, r.T, r.A])
            np.savetxt(path, data, delimiter=",",
                       header="wavelength_nm,R,T,A", comments="")
            self.statusBar().showMessage(f"Saved: {path}")

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    def _show_db(self):
        lines = []
        for mats_list in list(self.db._index.values())[:50]:
            m = mats_list[0]
            lines.append(f"{m.name:<18} n@550={m.n_ref:.4f}  k@550={m.k_ref:.4f}")
        QMessageBox.information(self, "Material Database", "\n".join(lines))

    def _show_about(self):
        QMessageBox.about(
            self, "About Stratoptic",
            "Stratoptic v0.3.0\n\n"
            "Thin Film Design & Simulation Platform\n"
            "Byrnes (2021) TMM + RefractiveIndex.info DB\n\n"
            "Author: Necmeddin\n"
            "Gazi University — Department of Photonics\n\n"
            "References:\n"
            "Byrnes, arXiv:1603.02720 (2021)\n"
            "Johnson & Christy, Phys. Rev. B 6 (1972)\n"
            "Born & Wolf, Principles of Optics (1999)"
        )


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Stratoptic")
    window = StratopticWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
