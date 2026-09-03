from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QCheckBox, QVBoxLayout, QWidget, QScrollArea
from data import Data
import locale

locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')

class ExemptStudents(QDialog):
    def __init__(self, parent, students, block):
        super().__init__(parent)
        self.setWindowTitle('Zwolnieni uczniowie')
        self.db: Data = parent.db
        self.block = block
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        scroll_area = QScrollArea()
        main_layout.addWidget(scroll_area)

        student_layout = QVBoxLayout()
        student_widget = QWidget()
        student_widget.setLayout(student_layout)
        scroll_area.setWidget(student_widget)
        scroll_area.setWidgetResizable(True)

        students.sort(key= lambda s: locale.strxfrm(s.name))
        for student in students:
            check_box = QCheckBox(student.name)
            check_box.setChecked(block in student.non_mandatory_blocks)
            check_box.toggled.connect(self.exempt_student(student))
            student_layout.addWidget(check_box)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        main_layout.addWidget(button_box)



    def exempt_student(self, student):
        def func(exempt):
            self.db.exempt_student_from_block(student, self.block, exempt)
        return func