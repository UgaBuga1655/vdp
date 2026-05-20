from tkinter import NO

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGridLayout, QLabel,\
      QSpinBox, QLineEdit, QMessageBox, QPushButton, QHBoxLayout
from functions import delete_layout
from data import Data, Classroom
from .classroom_tree_widget import ClassroomTreeWidget
from .distance_table import DistanceTable

class ClassroomsWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.db: Data = parent.db
        grid = QHBoxLayout(self)
        
        self.distances = DistanceTable(self)
        self.distances.load_data(self.db)
        grid.addWidget(self.distances)

        self.tree = ClassroomTreeWidget(self)
        self.tree.redraw_table.connect(self.distances.load_content)
        grid.addWidget(self.tree)


    def load_data(self, db):
        self.db = db
        self.distances.load_data(db)
        self.tree.load_data(db)
        # self.classroo
        # ms = self.db.all_classrooms()
        # for col in range(self.grid.columnCount()):
        #     for row in range(self.grid.rowCount()):
        #         item = self.grid.itemAtPosition(row, col)
        #         if item:
        #             item.widget().deleteLater()
        # for row, classroom in enumerate(self.classrooms):
        #     self.add_classroom_to_grid(row, classroom)


