from PyQt6.QtCore import QObject, pyqtSignal


class AppState(QObject):
    """Merkezi uygulama state'i. Degisikliklerde signal emit eder."""

    result_changed = pyqtSignal()
    structure_changed = pyqtSignal()
    theme_changed = pyqtSignal(dict)
    overlay_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._result = None
        self._structure = None
        self._theme = None
        self._overlay_results = []
        self._wavelengths = None

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

    @property
    def overlay_results(self): return self._overlay_results

    @property
    def wavelengths(self): return self._wavelengths

    @wavelengths.setter
    def wavelengths(self, val):
        self._wavelengths = val

    def add_overlay(self, result, structure, color):
        self._overlay_results.append((result, structure, color))
        if len(self._overlay_results) > 8:
            self._overlay_results.pop(0)
        self.overlay_changed.emit()

    def clear_overlays(self):
        self._overlay_results.clear()
        self.overlay_changed.emit()
