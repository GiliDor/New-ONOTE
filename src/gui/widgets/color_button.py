from PyQt6.QtWidgets import QPushButton, QColorDialog
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor


class ColorButton(QPushButton):
    """Unified color button with swatch and identical behavior to Preferences.

    Emits colorChanged with a hex string like '#RRGGBB'.
    """

    colorChanged = pyqtSignal(str)

    def __init__(self, initial_color: str = "#000000", parent=None, text: str = "Choose Color"):
        super().__init__(text, parent)
        try:
            self._color = QColor(initial_color)
        except Exception:
            self._color = QColor("#000000")
        self.setMinimumWidth(100)
        self._apply_style()
        self.clicked.connect(self._on_click)

    def _apply_style(self) -> None:
        hex_color = self._color.name()
        # Compute luminance for contrast text
        try:
            luminance = (0.299 * self._color.red() + 0.587 * self._color.green() + 0.114 * self._color.blue()) / 255.0
        except Exception:
            luminance = 0.0
        text_color = "#FFFFFF" if luminance < 0.5 else "#000000"
        self.setStyleSheet(f"background-color: {hex_color}; color: {text_color};")

    def _on_click(self) -> None:
        color = QColorDialog.getColor(
            self._color,
            self,
            "Choose Color",
            QColorDialog.ColorDialogOption.DontUseNativeDialog,
        )
        if color.isValid():
            self._color = color
            self._apply_style()
            try:
                self.colorChanged.emit(self._color.name())
            except Exception:
                pass

    def setColor(self, hex_color: str) -> None:
        try:
            c = QColor(hex_color)
            if c.isValid():
                self._color = c
                self._apply_style()
                self.colorChanged.emit(self._color.name())
        except Exception:
            pass

    def color(self) -> str:
        try:
            return self._color.name()
        except Exception:
            return "#000000"



