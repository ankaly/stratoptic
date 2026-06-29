"""
Stratoptic - Main Window (v1.0)
========================================================
Author      : Necmeddin
Institution : Gazi University, Department of Photonics
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QSplitter, QTableWidgetItem, QSplashScreen,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QActionGroup

from motor.rii_db import RIIDatabase
from motor.engine import TMMEngine
from motor.optimizer import OptimizeWorker
from motor.color import coating_color

from ui.theme import DARK, LIGHT, build_style, is_dark
from ui.plot_area import PlotArea
from ui.ribbon import Ribbon, SummaryBar
from ui.sidebar import Sidebar
from ui.splash import make_splash_pixmap
from ui import dialogs
from core.state import AppState

import matplotlib
matplotlib.use("QtAgg")


class StratopticWindow(QMainWindow):

    def __init__(self, splash=None):
        super().__init__()
        if splash:
            splash.showMessage("Indexing materials…",
                               Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                               QColor("#AAAAAA"))
        self.db = RIIDatabase("data/rii_db")
        self.state = AppState()
        self.state.theme = DARK if is_dark() else LIGHT
        self._overlay_palette = [
            "#FF453A","#0A84FF","#32D74B","#FFD60A",
            "#BF5AF2","#FF9F0A","#AC8E68","#30D5C8",
        ]
        self._worker = None
        self._user_datasets = []
        self._live_timer = QTimer(self)
        self._live_timer.setSingleShot(True)
        self._live_timer.setInterval(300)
        self._live_timer.timeout.connect(self._calculate)

        self.setWindowTitle("Stratoptic")
        self.setMinimumSize(1100, 680)
        self.resize(1500, 900)
        self.setStyleSheet(build_style(self.state.theme))
        self._build_menu()
        self._build_ui()
        self.statusBar().showMessage(
            "Stratoptic v1.0  ·  Licensed for: Gazi University Photonics Research Center")

    # ── Theme ──────────────────────────────────────────────────────────

    def _set_theme(self, mode):
        self.state.theme = (DARK if (mode == "dark" or (mode == "auto" and is_dark()))
                            else LIGHT)

    def _on_theme_changed(self, t):
        self.setStyleSheet(build_style(t))
        self.plot_area.apply_theme(t)
        self.ribbon.btn_theme_toggle.setText("☀" if t is DARK else "🌙")

    def _toggle_theme(self):
        self._set_theme("light" if self.state.theme is DARK else "dark")

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
        aud = QAction("Manage User Datasets…", self)
        aud.triggered.connect(self._manage_datasets); tom.addAction(aud)

        sem = mb.addMenu("Settings")
        self.live_preview_action = QAction("Live preview", self, checkable=True)
        self.live_preview_action.setChecked(True)
        sem.addAction(self.live_preview_action)

        hm = mb.addMenu("Help")
        ab = QAction("About Stratoptic", self)
        ab.triggered.connect(self._show_about); hm.addAction(ab)

    # ── UI assembly ────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget(); root.setObjectName("root")
        self.setCentralWidget(root)
        vl = QVBoxLayout(root)
        vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(0)

        t = self.state.theme
        self.ribbon = Ribbon(t)
        self.ribbon.calculate_requested.connect(self._calculate)
        self.ribbon.optimize_requested.connect(self._run_optimization)
        self.ribbon.theme_toggle_requested.connect(self._toggle_theme)
        self.ribbon.replot_requested.connect(self._replot)
        self.ribbon.overlay_cleared.connect(self._clear_overlay)
        vl.addWidget(self.ribbon)

        self.sumbar = SummaryBar(t)
        vl.addWidget(self.sumbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        self.sidebar = Sidebar(t, self.db)
        self.sidebar.status_message.connect(self.statusBar().showMessage)
        self.sidebar.dispersion_requested.connect(self._on_dispersion)
        self.sidebar.stack_refresh_requested.connect(self._on_stack_changed)
        splitter.addWidget(self.sidebar)

        self.plot_area = PlotArea(t)
        splitter.addWidget(self.plot_area)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 1200])
        splitter.setHandleWidth(2)
        vl.addWidget(splitter)

        self.state.theme_changed.connect(self._on_theme_changed)

    # ── Signal handlers ───────────────────────────────────────────────

    def _on_dispersion(self, mat):
        self.plot_area.disp_canvas.plot(mat, self.db)
        self.plot_area.btabs.setCurrentWidget(self.plot_area.disp_canvas)

    def _refresh_stack(self):
        try:
            self.plot_area.stack_canvas.plot(
                self.sidebar.build_structure(), self.db)
        except Exception:
            self.plot_area.stack_canvas._empty()

    def _on_stack_changed(self):
        self._refresh_stack()
        if self.live_preview_action.isChecked():
            self._live_timer.start()

    # ── Calculation ────────────────────────────────────────────────────

    def _get_pol(self):
        t = self.ribbon.combo_pol.currentText()
        if "s" in t: return "s"
        if "p" in t: return "p"
        return "unpolarized"

    def _calculate(self):
        try:
            st = self.sidebar.build_structure()
            wl = np.linspace(self.ribbon.spin_wl_min.value(),
                             self.ribbon.spin_wl_max.value(),
                             self.ribbon.spin_pts.value())
            pol = self._get_pol(); ang = self.ribbon.spin_angle.value()
            result = TMMEngine(st).calculate(wl, angle=ang,
                                              polarization=pol,
                                              substrate_thickness_mm=1.0)
            if self.ribbon.chk_overlay.isChecked() and self.state.result is not None:
                n = len(self.state.overlay_results)
                color = self._overlay_palette[n % len(self._overlay_palette)]
                self.state.add_overlay(self.state.result, self.state.structure, color)
            self.state.wavelengths = wl
            self.state.structure = st
            self.state.result = result
            self.plot_area.canvas.plot(
                result, self.ribbon.chk_R.isChecked(),
                self.ribbon.chk_T.isChecked(), self.ribbon.chk_A.isChecked(),
                st, overlays=self.state.overlay_results)
            self.sumbar.update_stats(result.R.mean(), result.T.mean(), result.A.mean())
            self.sumbar.update_swatches(result, coating_color)
            self.sumbar.lbl_info.setText(
                f"λ {wl[0]:.0f}–{wl[-1]:.0f} nm  ·  {len(wl)} pts  ·  {pol}  ·  θ={ang}°")
            self.plot_area.update_results(wl, result)
            self.plot_area.stack_canvas.plot(st, self.db)
            self._update_efield(st, wl, pol, ang)
            self.plot_area.btabs.setCurrentIndex(0)
            self.statusBar().showMessage("Calculation complete.")
        except Exception as e:
            import traceback
            self.statusBar().showMessage(f"Error: {e}")
            print(traceback.format_exc())

    def _update_efield(self, st, wl, pol, ang):
        wl_mid = float(wl[len(wl) // 2])
        ef_pol = pol if pol != "unpolarized" else "s"
        try:
            ef = TMMEngine(st).electric_field(wl_mid, angle=ang, polarization=ef_pol)
            self.plot_area.efield_canvas.plot(ef, wl_mid)
        except Exception:
            self.plot_area.efield_canvas._empty()

    def _clear_overlay(self):
        self.state.clear_overlays()
        self._replot()

    def _replot(self):
        if self.state.result:
            self.plot_area.canvas.plot(
                self.state.result, self.ribbon.chk_R.isChecked(),
                self.ribbon.chk_T.isChecked(), self.ribbon.chk_A.isChecked(),
                self.state.structure, overlays=self.state.overlay_results)

    # ── Optimization ───────────────────────────────────────────────────

    def _run_optimization(self):
        oi = self.sidebar.get_opt_idx()
        if not oi:
            self.statusBar().showMessage("No layers selected for optimization.")
            return
        conds = self.sidebar.get_conditions(self.ribbon.spin_wl_min.value(),
                                            self.ribbon.spin_wl_max.value())
        bounds = [(self.ribbon.spin_d_min.value(),
                   self.ribbon.spin_d_max.value())] * len(oi)
        self.ribbon.btn_opt.setEnabled(False)
        cs = "  ·  ".join([f"{m} {g} [{w0:.0f}–{w1:.0f}nm]×{wt}"
                            for w0,w1,m,g,wt in conds])
        self.statusBar().showMessage(f"Optimizing {len(oi)} layer(s)  ·  {cs}")
        self._worker = OptimizeWorker(
            self.sidebar.build_structure_opt, oi, bounds, conds,
            self._get_pol(), self.ribbon.spin_angle.value())
        self._worker.progress.connect(self.statusBar().showMessage)
        self._worker.iteration.connect(self._on_opt_iteration)
        self._worker.finished.connect(self._on_opt_done)
        self._worker.start()

    def _apply_opt_thicknesses(self, thicknesses):
        for i, row in enumerate(self.sidebar.get_opt_idx()):
            self.sidebar.layer_table.setItem(
                row, 1, QTableWidgetItem(f"{thicknesses[i]:.1f}"))

    def _on_opt_iteration(self, thicknesses, obj_val):
        self._apply_opt_thicknesses(thicknesses)
        self.statusBar().showMessage(
            f"Optimizing…  obj={obj_val:.4f}  ·  " +
            "  ".join([f"L{i+1}={d:.1f}nm" for i, d in enumerate(thicknesses)]))
        self._calculate()

    def _on_opt_done(self, thicknesses, obj_val):
        self.ribbon.btn_opt.setEnabled(True)
        self._apply_opt_thicknesses(thicknesses)
        self.statusBar().showMessage(
            f"Done  ·  obj={obj_val:.4f}  ·  " +
            "  ".join([f"L{i+1}={d:.1f}nm" for i,d in enumerate(thicknesses)]))
        self._calculate()

    # ── Dialogs ────────────────────────────────────────────────────────

    def _export_png(self):
        dialogs.export_png(self, self.state.result, self.plot_area.canvas)

    def _export_csv(self):
        dialogs.export_csv(self, self.state.result)

    def _import_dataset(self):
        combos = [self.sidebar.combo_mat, self.sidebar.combo_inc,
                  self.sidebar.combo_sub]
        dialogs.import_dataset(self, self.db, combos,
                               self._user_datasets, self.statusBar())

    def _manage_datasets(self):
        combos = [self.sidebar.combo_mat, self.sidebar.combo_inc,
                  self.sidebar.combo_sub]
        dialogs.manage_datasets_dialog(self, self.db, combos,
                                       self._user_datasets, self.statusBar())

    def _show_db(self):
        dialogs.show_db_dialog(self, self.db)

    def _show_about(self):
        dialogs.show_about_dialog(self)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Stratoptic")

    splash = QSplashScreen(make_splash_pixmap())
    splash.show()
    app.processEvents()

    window = StratopticWindow(splash=splash)
    window.show()
    splash.finish(window)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
