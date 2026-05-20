from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QSize

 
class VerticalLabel(QLabel):

    def __init__(self, name, alignment=None):
        super().__init__(name)
        if not alignment:
            alignment = Qt.AlignLeft | Qt.AlignVCenter
        self.al = alignment

    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        return QSize(size.height(), size.width())

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(size.height()+10, size.width()+15)
    

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(0, self.height()-5)
        painter.rotate(270)
        painter.drawText(0, 0, self.height(), self.width(),
                         self.al, self.text())
       