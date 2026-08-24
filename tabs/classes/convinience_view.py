from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QHBoxLayout, QDialog, QDialogButtonBox, \
      QPushButton, QLabel, QDialogButtonBox, QMessageBox, QCheckBox, QColorDialog, QLineEdit, QSpinBox
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QColor, QCursor
from models import Subject

from week_view import MyView

class ConvinienceView(MyView):
    def __init__(self, subject:Subject, parent = ..., flags = ...):
        super().__init__(parent, flags)
        self.subject = subject

    def draw(self):
        super().draw()

    def load_day(self, n: int):
        teachers = self.subject.teachers
        av = 1<<17-1
        for teacher in teachers

