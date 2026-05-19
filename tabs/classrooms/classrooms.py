from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGridLayout, QLabel,\
      QSpinBox, QLineEdit, QMessageBox, QPushButton
from functions import delete_layout
from data import Data, Classroom
from .classroom_tree_widget import ClassroomTreeWidget

class ClassroomsWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.db: Data = parent.db
        self.setLayout(QVBoxLayout())

        self.new_name = QLineEdit(self)
        self.layout().addWidget(self.new_name)
        self.new_name.setPlaceholderText('Nazwa klasy')
        self.tree = ClassroomTreeWidget(self)
        self.layout().addWidget(self.tree)
        self.new_name.returnPressed.connect(self.create_classroom_group)


        # self.grid = QGridLayout()
        # self.layout().addLayout(self.grid)
        # self.grid.setColumnStretch(4, 1)
        # self.layout().addStretch()
        # self.classrooms = []
        # self.load_data(self.db)
        # self.setLayout(self.grid)

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

    def add_classroom_to_grid(self, row, classroom: Classroom):
        self.grid.addWidget(QLabel(classroom.name), row, 0)

        student_count = QSpinBox()
        student_count.setValue(classroom.capacity)
        student_count.valueChanged.connect(self.set_capacity(classroom))
        self.grid.addWidget(student_count, row, 1)
        
        allow_lessons = QCheckBox('Przypisuj lekcje')
        allow_lessons.setChecked(classroom.allow_lessons)
        allow_lessons.toggled.connect(self.set_classroom_allow_lessons(classroom))
        self.grid.addWidget(allow_lessons, row, 2)

        del_btn = QPushButton('X')
        del_btn.clicked.connect(self.del_classroom(classroom))
        self.grid.addWidget(del_btn, row, 3)

    def add_classroom(self):
        name_box: QLineEdit = self.sender()
        name = name_box.text()
        if not name:
            return
        if name in [c.name for c in self.classrooms]:
            QMessageBox.warning(self, 'Uwaga', 'Takie pomieszczenie już istnieje')
            return
        classroom = self.db.create_classroom(name)
        row = self.grid.rowCount()
        self.add_classroom_to_grid(row, classroom)
        name_box.clear()

    def set_capacity(self, classroom):
        def func():
            cap = self.sender().value()
            self.db.update_classroom_capacity(classroom, cap)
        return func
    
    def del_classroom(self, classroom):
        def func():
            self.db.delete_classroom(classroom)
            self.load_data(self.db)
        return func
    
    def set_classroom_allow_lessons(self, classroom):
        def func(allow):
            self.db.update_classroom_allow_lessons(classroom, allow)
        return func


    def create_classroom_group(self):
        self.tree.create_classroom_group(self.new_name.text())
