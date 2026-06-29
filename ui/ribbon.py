from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QDoubleSpinBox, QSpinBox,
    QFrame, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.theme import DARK, sec, muted, vdiv


class Ribbon(QWidget):

    calculate_requested = pyqtSignal()
    optimize_requested = pyqtSignal()
    theme_toggle_requested = pyqtSignal()
    replot_requested = pyqtSignal()
    overlay_cleared = pyqtSignal()
    params_changed = pyqtSignal()

    def __init__(self, theme):
        super().__init__()
        self._t = theme
        self.setObjectName("ribbon")
        self.setFixedHeight(92)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(16, 0, 12, 0); hl.setSpacing(0)

        # App identity
        id_w = QWidget()
        id_l = QVBoxLayout(id_w); id_l.setContentsMargins(0, 0, 0, 0); id_l.setSpacing(1)
        id_l.addStretch()
        name = QLabel("STRATOPTIC"); name.setObjectName("appname")
        sub = QLabel("Thin Film Simulation Platform"); sub.setObjectName("appsub")
        id_l.addWidget(name); id_l.addWidget(sub)
        id_l.addStretch()
        hl.addWidget(id_w)
        hl.addSpacing(16)
        hl.addWidget(vdiv(theme))
        hl.addSpacing(14)

        # ── Calculation section ──────────────────────────────────────
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

        for w in [self.spin_wl_min, self.spin_wl_max, self.spin_pts]:
            w.valueChanged.connect(self.params_changed)
        self.spin_angle.valueChanged.connect(self.params_changed)
        self.combo_pol.currentTextChanged.connect(self.params_changed)

        hl.addWidget(calc_w)
        hl.addSpacing(10)
        hl.addWidget(vdiv(theme))
        hl.addSpacing(14)

        # ── Optimization section ─────────────────────────────────────
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
        self.btn_opt.clicked.connect(self.optimize_requested)
        opt_hint = muted("Check 'Opt' column in layer table")
        opt_l.addWidget(opt_hint)
        opt_l.addWidget(self.btn_opt)

        hl.addWidget(opt_w)
        hl.addSpacing(10)
        hl.addWidget(vdiv(theme))
        hl.addSpacing(12)

        # ── Show + Calculate ─────────────────────────────────────────
        right_w = QWidget()
        right_l = QVBoxLayout(right_w)
        right_l.setContentsMargins(0, 8, 0, 4); right_l.setSpacing(8)
        right_l.addStretch()

        show_r = QHBoxLayout(); show_r.setSpacing(8)
        show_r.addWidget(muted("Show:"))
        self.chk_R = QCheckBox("R"); self.chk_R.setChecked(True)
        self.chk_T = QCheckBox("T"); self.chk_T.setChecked(True)
        self.chk_A = QCheckBox("A"); self.chk_A.setChecked(True)
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
            chk.stateChanged.connect(self.replot_requested)
            show_r.addWidget(chk)
        show_r.addSpacing(12)
        self.chk_overlay = QCheckBox("Overlay")
        self.chk_overlay.setStyleSheet(
            "QCheckBox{color:#FFD60A;font-weight:700;spacing:5px;}"
            "QCheckBox::indicator{background:#FFD60A25;border:1.5px solid #FFD60A88;border-radius:4px;width:14px;height:14px;}"
            "QCheckBox::indicator:hover{border-color:#FFD60A;}"
            "QCheckBox::indicator:checked{background:#FFD60A;border-color:#FFD60A;}"
        )
        show_r.addWidget(self.chk_overlay)
        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("ghost")
        btn_clear.setFixedWidth(48)
        btn_clear.clicked.connect(self.overlay_cleared)
        show_r.addWidget(btn_clear)
        right_l.addLayout(show_r)

        self.btn_calc = QPushButton("Calculate")
        self.btn_calc.setObjectName("calc")
        self.btn_calc.clicked.connect(self.calculate_requested)
        right_l.addWidget(self.btn_calc)

        self.btn_theme_toggle = QPushButton("☀" if theme is DARK else "🌙")
        self.btn_theme_toggle.setObjectName("ghost")
        self.btn_theme_toggle.setFixedSize(30, 30)
        self.btn_theme_toggle.clicked.connect(self.theme_toggle_requested)
        right_l.addWidget(self.btn_theme_toggle)
        right_l.addStretch()
        hl.addWidget(right_w)


class SummaryBar(QWidget):

    def __init__(self, theme):
        super().__init__()
        self.setObjectName("sumbar"); self.setFixedHeight(44)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(20, 0, 20, 0); hl.setSpacing(0)
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
            kl = QLabel(label); kl.setObjectName("statkey")
            cl.addWidget(val); cl.addWidget(kl)
            self._sw[key] = val; hl.addWidget(cell)
            if key != "A":
                sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(
                    f"background:{theme['line0']};max-width:1px;border:none;")
                hl.addSpacing(18); hl.addWidget(sep); hl.addSpacing(18)
        # Color swatches (reflection + transmission)
        hl.addSpacing(18)
        for attr, label in [("swatch_r", "R"), ("swatch_t", "T")]:
            sl = QHBoxLayout(); sl.setSpacing(5)
            swatch = QLabel()
            swatch.setFixedSize(16, 16)
            swatch.setStyleSheet("background:#333;border-radius:3px;border:1px solid #555;")
            lbl_s = QLabel(label); lbl_s.setObjectName("statkey")
            sl.addWidget(swatch); sl.addWidget(lbl_s)
            setattr(self, attr, swatch)
            hl.addLayout(sl)
            hl.addSpacing(12)
        hl.addStretch()
        self.lbl_info = QLabel(""); self.lbl_info.setObjectName("statkey")
        self.lbl_info.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hl.addWidget(self.lbl_info)

    def update_stats(self, R_avg, T_avg, A_avg):
        self._sw["R"].setText(f"{R_avg*100:.2f}%")
        self._sw["T"].setText(f"{T_avg*100:.2f}%")
        self._sw["A"].setText(f"{A_avg*100:.2f}%")

    def update_swatches(self, result, coating_color_fn):
        for mode, widget in [('reflection', self.swatch_r),
                              ('transmission', self.swatch_t)]:
            try:
                c = coating_color_fn(result, mode=mode)
                hex_c = c['hex']
                x, y = c['xy']
                R, G, B = c['sRGB']
                widget.setStyleSheet(
                    f"background:{hex_c};border-radius:3px;border:1px solid #555;")
                widget.setToolTip(
                    f"{'Reflection' if mode=='reflection' else 'Transmission'} color\n"
                    f"xy = ({x:.4f}, {y:.4f})\n"
                    f"sRGB = ({R}, {G}, {B})\n"
                    f"{hex_c}")
            except Exception:
                pass
