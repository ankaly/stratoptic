from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPixmap, QPainter, QFont

from ui.theme import DARK


def make_splash_pixmap():
    W, H = 500, 300
    bg   = QColor(DARK["win"])
    acc  = QColor(DARK["accent"])
    px   = QPixmap(W, H)
    px.fill(bg)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # arka plan hafif gradient çizgisi
    p.setPen(QColor(DARK["line1"]))
    p.drawLine(0, H - 56, W, H - 56)

    # STRATOPTIC
    f = QFont("SF Pro Display", 42, QFont.Weight.Bold)
    p.setFont(f)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(QRect(0, 60, W, 70), Qt.AlignmentFlag.AlignHCenter, "STRATOPTIC")

    # alt başlık
    f.setPointSize(13); f.setWeight(QFont.Weight.Normal)
    p.setFont(f)
    p.setPen(acc)
    p.drawText(QRect(0, 138, W, 30), Qt.AlignmentFlag.AlignHCenter,
               "Thin Film Simulation Platform")

    # küçük yazı
    f.setPointSize(10)
    p.setFont(f)
    p.setPen(QColor(DARK["t2"]))
    p.drawText(QRect(0, 172, W, 24), Qt.AlignmentFlag.AlignHCenter,
               "Gazi University  ·  Photonics")

    # status
    p.setPen(QColor(DARK["t2"]))
    f.setPointSize(9)
    p.setFont(f)
    p.drawText(QRect(0, H - 44, W, 24), Qt.AlignmentFlag.AlignHCenter,
               "Loading database…")

    p.end()
    return px
