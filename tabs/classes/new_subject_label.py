from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize

class NewSubjectLabel(QPushButton):
    def sizeHint(self):
        return self.fontMetrics().size(0, self.text()) + QSize(12, 6)
