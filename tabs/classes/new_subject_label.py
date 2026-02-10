from .subject_label import SubjectLabel
from .subjects import SubjectsWindow
from PyQt5.QtWidgets import QPushButton, QStyleOptionButton, QStyle
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QSize, Qt

class NewSubjectLabel(QPushButton):
    def sizeHint(self):
        return self.fontMetrics().size(0, self.text()) + QSize(12, 6)
