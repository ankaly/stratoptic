from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QTabWidget,
    QTableWidget, QHeaderView,
)
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from ui.canvases import SpectrumCanvas, DispersionCanvas, StackCanvas, EFieldCanvas


class PlotArea(QWidget):

    def __init__(self, theme):
        super().__init__()
        self.setObjectName("plotarea")
        vl = QVBoxLayout(self)
        vl.setContentsMargins(8, 4, 8, 4); vl.setSpacing(4)

        vsplit = QSplitter(Qt.Orientation.Vertical)
        vsplit.setChildrenCollapsible(False)

        # Spectrum + toolbar
        self.canvas = SpectrumCanvas(theme)
        nav = NavigationToolbar(self.canvas, self)
        for action in nav.actions():
            if action.text() in ("Subplots", "Customize"):
                nav.removeAction(action)
        spec_w = QWidget()
        sl = QVBoxLayout(spec_w)
        sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(0)
        sl.addWidget(self.canvas)
        sl.addWidget(nav)
        vsplit.addWidget(spec_w)

        # Bottom tabs
        self.btabs = QTabWidget()
        self.btabs.setDocumentMode(True)
        self.btabs.tabBar().setExpanding(True)

        self.stack_canvas = StackCanvas(theme)
        self.btabs.addTab(self.stack_canvas, "Layer Stack")

        self.res_table = QTableWidget(0, 4)
        self.res_table.setHorizontalHeaderLabels(["λ (nm)", "R (%)", "T (%)", "A (%)"])
        self.res_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.res_table.setAlternatingRowColors(True)
        self.res_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.btabs.addTab(self.res_table, "Spectral Data")

        self.disp_canvas = DispersionCanvas(theme)
        self.btabs.addTab(self.disp_canvas, "Dispersion")

        self.efield_canvas = EFieldCanvas(theme)
        self.btabs.addTab(self.efield_canvas, "E-Field")

        vsplit.addWidget(self.btabs)
        vsplit.setSizes([540, 200])
        vl.addWidget(vsplit)

    def apply_theme(self, theme):
        self.canvas.apply_theme(theme)
        self.stack_canvas.apply_theme(theme)
        self.disp_canvas.apply_theme(theme)
        self.efield_canvas.apply_theme(theme)
