from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


class AppState(QObject):
    """Merkezi uygulama state'i. Değişikliklerde signal emit eder."""

    result_changed = pyqtSignal()          # hesaplama sonucu değişti
    structure_changed = pyqtSignal()       # katman yapısı değişti
    theme_changed = pyqtSignal(dict)       # tema değişti

    def __init__(self):
        super().__init__()
        self._result = None        # TMMResult
        self._structure = None     # Structure
        self._theme = None         # DARK veya LIGHT dict

    @property
    def result(self): return self._result

    @result.setter
    def result(self, val):
        self._result = val
        self.result_changed.emit()

    @property
    def structure(self): return self._structure

    @structure.setter
    def structure(self, val):
        self._structure = val
        self.structure_changed.emit()

    @property
    def theme(self): return self._theme

    @theme.setter
    def theme(self, val):
        self._theme = val
        self.theme_changed.emit(val)
