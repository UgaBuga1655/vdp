from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QWidget


class Color(QWidget):
    def __init__(self, color, brighten=False):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        color = QColor(color)
        if brighten:
            color = color.lighter(130)
        palette.setColor(QPalette.ColorRole.Window, color)
        self.setPalette(palette)