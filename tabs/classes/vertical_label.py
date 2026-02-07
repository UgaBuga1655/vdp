from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QSize

class VerticalLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # self.setMargin(10)

    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        return QSize(size.height(), size.width())

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(size.height()+10, size.width()+10)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(0, self.height()-5)
        painter.rotate(275)
        painter.drawText(0, 0, self.height(), self.width(),
                         Qt.AlignLeft | Qt.AlignVCenter, self.text())