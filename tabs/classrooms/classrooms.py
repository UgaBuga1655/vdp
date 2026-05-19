from tkinter import NO

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGridLayout, QLabel,\
      QSpinBox, QLineEdit, QMessageBox, QPushButton
from functions import delete_layout
from data import Data, Classroom
from .classroom_tree_widget import ClassroomTreeWidget
from .distance_table import DistanceTable

class ClassroomsWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.db: Data = parent.db
        self.setLayout(QVBoxLayout())
        self.distance_table = None

        # self.new_name = QLineEdit(self)
        # self.layout().addWidget(self.new_name)
        # self.new_name.setPlaceholderText('Nazwa klasy')
        btn = QPushButton('Odległości')
        btn.clicked.connect(self.distances)
        self.layout().addWidget(btn)

        self.tree = ClassroomTreeWidget(self)
        self.layout().addWidget(self.tree)
        # self.new_name.returnPressed.connect(self.create_classroom_group)


    def load_data(self, db):
        self.db = db
        # self.classrooms = self.db.all_classrooms()
        # for col in range(self.grid.columnCount()):
        #     for row in range(self.grid.rowCount()):
        #         item = self.grid.itemAtPosition(row, col)
        #         if item:
        #             item.widget().deleteLater()
        # for row, classroom in enumerate(self.classrooms):
        #     self.add_classroom_to_grid(row, classroom)

    def distances(self):
        if not self.distance_table:
            self.distance_table = DistanceTable(self)
        self.distance_table.show()
        self.distance_table.load_data(self.db)
