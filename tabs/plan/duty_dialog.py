from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QPushButton, QDialogButtonBox
from numpy import delete
from models import CustomBlock
from data import Data

class DutyDialog(QDialog):
    def __init__(self, custom_block, db: Data):
        super().__init__()
        self.custom_block = custom_block
        self.db = db
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.duties = QGridLayout()
        layout.addLayout(self.duties)
        for duty in custom_block.duties:
            self.place_duty(duty)
            
        row = QHBoxLayout()
        layout.addLayout(row)
        new_button = QPushButton('+')
        new_button.clicked.connect(self.add_duty)
        row.addWidget(new_button)
        row.addStretch()

        buttonBox = QDialogButtonBox()
        row.addWidget(buttonBox)

        buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)

    def add_duty(self):
        duty = self.db.new_duty(self.custom_block)
        self.place_duty(duty)


    def place_duty(self, duty):
        row = self.duties.rowCount()

        classroom_select = QComboBox()
        classroom_select.addItem('---', None)
        for classroom in self.db.all_classrooms():
            classroom_select.addItem(classroom.name, classroom)
        classroom_select.currentIndexChanged.connect(
            self.update_duty_classroom(duty, classroom_select)
        )
        self.duties.addWidget(classroom_select, row, 0)
        if duty.classroom:
            classroom_select.setCurrentText(duty.classroom.name)

        teacher_select = QComboBox()
        teacher_select.addItem('---', None)
        for teacher in self.db.read_all_teachers():
            teacher_select.addItem(teacher.name, teacher)
        teacher_select.currentIndexChanged.connect(
            self.update_duty_teacher(duty, teacher_select)
        )
        self.duties.addWidget(teacher_select, row, 1)
        if duty.teacher:
            teacher_select.setCurrentText(duty.teacher.name)

        del_btn = QPushButton('X')
        del_btn.setFixedWidth(20)
        del_btn.clicked.connect(self.delete_duty(duty,
            [teacher_select, classroom_select, del_btn]))
        self.duties.addWidget(del_btn, row, 2)


    def update_duty_classroom(self, duty, select):
        def func():
            classroom = select.currentData()
            self.db.update_duty_classroom(duty, classroom)
        return func
    
    def update_duty_teacher(self, duty, select):
        def func():
            teacher = select.currentData()
            self.db.update_duty_teacher(duty, teacher)
        return func
    
    def delete_duty(self, duty, widgets):
        def func():
            self.db.delete_duty(duty)
            for widget in widgets:
                widget.deleteLater()
        return func