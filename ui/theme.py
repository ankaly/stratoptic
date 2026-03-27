from PyQt6.QtWidgets import QApplication, QLabel, QFrame
from PyQt6.QtGui import QPalette

DARK = {
    "win":      "#141416",
    "panel":    "#1E1E21",
    "raised":   "#252529",
    "input":    "#2E2E33",
    "hover":    "#38383E",
    "line0":    "#27272C",
    "line1":    "#333339",
    "line2":    "#44444C",
    "t0":       "#EDEDF2",
    "t1":       "#A8A8B0",
    "t2":       "#636368",
    "accent":   "#0A84FF",
    "accentH":  "#3B9EFF",
    "accentP":  "#0060D0",
    "danger":   "#FF453A",
    "success":  "#32D74B",
    "warn":     "#FFD60A",
    "plot_bg":  "#141416",
    "plot_ax":  "#1A1A1E",
    "plot_grid":"#252529",
}

LIGHT = {
    "win":      "#F0F0F5",
    "panel":    "#FFFFFF",
    "raised":   "#F5F5FA",
    "input":    "#EBEBF0",
    "hover":    "#E0E0E8",
    "line0":    "#E0E0E8",
    "line1":    "#CCCCDA",
    "line2":    "#BBBBCA",
    "t0":       "#111115",
    "t1":       "#505058",
    "t2":       "#9090A0",
    "accent":   "#007AFF",
    "accentH":  "#3395FF",
    "accentP":  "#0055CC",
    "danger":   "#FF3B30",
    "success":  "#34C759",
    "warn":     "#FF9500",
    "plot_bg":  "#F0F0F5",
    "plot_ax":  "#FFFFFF",
    "plot_grid":"#E0E0E8",
}


def build_style(t):
    # NavigationToolbar background fix — always matches plot area
    return f"""
QWidget {{
    font-family: -apple-system, 'SF Pro Text', 'Segoe UI', 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
    font-size: 12px;
    color: {t['t0']};
    background: transparent;
}}
QMainWindow {{ background: {t['win']}; }}
QWidget#root {{ background: {t['win']}; }}
QWidget#sidebar {{
    background: {t['panel']};
    border-right: 1px solid {t['line0']};
}}
QWidget#ribbon {{
    background: {t['raised']};
    border-bottom: 1px solid {t['line0']};
}}
QWidget#sumbar {{
    background: {t['panel']};
    border-bottom: 1px solid {t['line0']};
}}
QWidget#plotarea {{ background: {t['win']}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

/* ── Section labels ── */
QLabel#sec {{
    color: {t['accent']};
    font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
}}
QLabel#muted {{
    color: {t['t2']}; font-size: 11px;
}}
QLabel#appname {{
    color: {t['t0']}; font-size: 15px; font-weight: 800; letter-spacing: -0.3px;
}}
QLabel#appsub {{
    color: {t['accent']}; font-size: 10px; font-weight: 600; letter-spacing: 0.4px;
}}
QLabel#statval {{
    font-size: 15px; font-weight: 700;
}}
QLabel#statkey {{
    color: {t['t2']}; font-size: 10px;
}}

/* ── Primary button ── */
QPushButton {{
    background: {t['accent']};
    color: #FFFFFF;
    border: none;
    border-radius: 7px;
    padding: 0 16px;
    font-weight: 600;
    font-size: 12px;
    min-height: 30px;
}}
QPushButton:hover {{
    background: {t['accentH']};
}}
QPushButton:pressed {{
    background: {t['accentP']};
}}
QPushButton:disabled {{
    background: {t['input']}; color: {t['t2']};
}}

/* ── Ghost button ── */
QPushButton#ghost {{
    background: {t['input']};
    color: {t['t0']};
    border: 1px solid {t['line2']};
    border-radius: 7px;
}}
QPushButton#ghost:hover {{
    background: {t['hover']};
    border-color: {t['accent']};
    color: {t['t0']};
}}
QPushButton#ghost:pressed {{
    background: {t['line1']};
}}

/* ── Remove / danger button ── */
QPushButton#rm {{
    background: transparent;
    color: {t['danger']};
    border: 1px solid {t['danger']}55;
    border-radius: 5px;
    padding: 0 6px;
    min-height: 20px;
    font-size: 11px;
    font-weight: 600;
}}
QPushButton#rm:hover {{
    background: {t['danger']}20;
    border-color: {t['danger']};
}}

/* ── Warn / optimize button ── */
QPushButton#warn {{
    background: {t['warn']}15;
    color: {t['warn']};
    border: 1px solid {t['warn']}55;
    border-radius: 7px;
    font-weight: 700;
    padding: 0 16px;
    min-height: 30px;
}}
QPushButton#warn:hover {{
    background: {t['warn']}30;
    border-color: {t['warn']};
}}
QPushButton#warn:disabled {{
    background: {t['input']}; color: {t['t2']}; border-color: {t['line2']};
}}

/* ── Calculate button ── */
QPushButton#calc {{
    background: {t['accent']};
    color: white;
    border-radius: 7px;
    font-weight: 700;
    font-size: 13px;
    min-height: 34px;
    padding: 0 22px;
}}
QPushButton#calc:hover {{ background: {t['accentH']}; }}
QPushButton#calc:pressed {{ background: {t['accentP']}; }}

/* ── Inputs ── */
QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {t['input']};
    color: {t['t0']};
    border: 1px solid {t['line2']};
    border-radius: 6px;
    padding: 0 8px;
    min-height: 28px;
    selection-background-color: {t['accent']};
}}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {t['accent']}80;
    background: {t['hover']};
}}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {t['accent']};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {t['raised']};
    color: {t['t0']};
    border: 1px solid {t['line1']};
    border-radius: 6px;
    selection-background-color: {t['accent']};
    padding: 2px;
    outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: {t['hover']}; border: none; width: 16px; border-radius: 3px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {t['line2']};
}}

/* ── Table ── */
QTableWidget {{
    background: {t['panel']};
    color: {t['t0']};
    border: 1px solid {t['line1']};
    border-radius: 8px;
    gridline-color: {t['line0']};
    alternate-background-color: {t['raised']};
    selection-background-color: {t['accent']}22;
    selection-color: {t['t0']};
    outline: none;
}}
QTableWidget::item {{ padding: 2px 6px; }}
QTableWidget::item:hover {{ background: {t['hover']}40; }}
QHeaderView::section {{
    background: {t['input']};
    color: {t['t2']};
    border: none;
    border-bottom: 1px solid {t['line1']};
    padding: 5px 6px;
    font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: none;
    border-top: 1px solid {t['line1']};
    background: {t['panel']};
}}
QTabBar {{
    background: {t['raised']};
}}
QTabBar::tab {{
    background: {t['raised']};
    color: {t['t2']};
    border: none;
    padding: 8px 18px;
    font-size: 11px; font-weight: 600;
    min-width: 90px;
}}
QTabBar::tab:selected {{
    background: {t['panel']};
    color: {t['accent']};
    border-bottom: 2px solid {t['accent']};
}}
QTabBar::tab:hover:!selected {{
    color: {t['t1']};
    background: {t['hover']};
}}

/* ── Checkbox ── */
QCheckBox {{ color: {t['t0']}; spacing: 6px; }}
QCheckBox::indicator {{
    width: 15px; height: 15px;
    border-radius: 4px;
    border: 1.5px solid {t['line2']};
    background: {t['input']};
}}
QCheckBox::indicator:hover {{ border-color: {t['accent']}; }}
QCheckBox::indicator:checked {{
    background: {t['accent']}; border-color: {t['accent']};
}}

/* ── Menu ── */
QMenuBar {{
    background: {t['raised']}; color: {t['t0']};
    border-bottom: 1px solid {t['line0']}; padding: 2px 8px;
}}
QMenuBar::item {{ padding: 4px 12px; border-radius: 5px; }}
QMenuBar::item:selected {{ background: {t['hover']}; }}
QMenu {{
    background: {t['raised']}; color: {t['t0']};
    border: 1px solid {t['line1']}; border-radius: 10px; padding: 5px;
}}
QMenu::item {{ padding: 7px 22px; border-radius: 5px; }}
QMenu::item:selected {{ background: {t['accent']}; color: white; }}
QMenu::separator {{ height: 1px; background: {t['line0']}; margin: 4px 2px; }}

/* ── Status bar ── */
QStatusBar {{
    background: {t['raised']}; color: {t['t2']};
    border-top: 1px solid {t['line0']};
    font-size: 11px; padding: 2px 14px;
}}

/* ── NavigationToolbar ── */
QToolBar {{
    background: {t['win']};
    border: none;
    spacing: 2px;
    padding: 2px 4px;
}}
QToolBar QToolButton {{
    background: transparent;
    color: {t['t1']};
    border: none;
    border-radius: 5px;
    padding: 4px;
    min-width: 24px; min-height: 24px;
}}
QToolBar QToolButton:hover {{
    background: {t['hover']};
    color: {t['t0']};
}}
QToolBar QToolButton:pressed {{
    background: {t['line1']};
}}
QToolBar QToolButton:checked {{
    background: {t['accent']}22;
    color: {t['accent']};
}}

/* ── Splitter ── */
QSplitter::handle {{ background: {t['line0']}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}

/* ── Scrollbar ── */
QScrollBar:vertical {{
    background: transparent; width: 6px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t['line2']}; border-radius: 3px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {t['t2']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


def is_dark():
    return QApplication.instance().palette().color(
        QPalette.ColorRole.Window).lightness() < 128


def sec(text):
    l = QLabel(text.upper()); l.setObjectName("sec"); return l


def muted(text):
    l = QLabel(text); l.setObjectName("muted"); return l


def hdiv(t):
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background:{t['line0']};max-height:1px;border:none;"); return f


def vdiv(t):
    f = QFrame(); f.setFrameShape(QFrame.Shape.VLine)
    f.setStyleSheet(f"background:{t['line0']};max-width:1px;border:none;"); return f
