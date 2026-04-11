from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QButtonGroup, QLineEdit, QScrollArea, QVBoxLayout, QSizePolicy

from data import Data

class ImportStudentsWidget(QWidget):
    def __init__(self, parent, students, class_):
        super().__init__(parent)
        self.db: Data = parent.db
        self.students = dict()

        scroll_area = QScrollArea()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_area)
        self.grid = QGridLayout()
        container = QWidget()
        container.setLayout(self.grid)
        scroll_area.setWidget(container)
        scroll_area.setWidgetResizable(True)
        default_subclass = class_.subclasses[0]
        # self.students = {name: {'subclass': default_subclass, 'name': name} for name in student_names}
        # student_names.sort()
        for row, student in enumerate(students):
            name, subjects = student
            # guess subclass
            # subclass_names = {subclass.name.upper() for subclass in class_.subclasses}
            subclasses = {subclass.name.upper(): subclass for subclass in class_.subclasses}
            students_subclass = default_subclass
            for subject_name in subjects:
                last_letter = subject_name[-1].upper()
                last_word_is_short = len(subject_name.split()[-1]) <= 2
                if last_word_is_short and last_letter in subclasses:
                    # print(last_letter)
                    students_subclass = subclasses[last_letter]
                    break

            student = self.db.create_student(name, students_subclass)
            self.students[name] = student

            buttons = QButtonGroup(self)
            buttons.setExclusive(True)
            for col, subclass in enumerate(class_.subclasses):
                btn = QPushButton(subclass.name.upper())
                btn.setFixedSize(20,20)
                btn.setCheckable(True)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f0f0f0;
                    }
                    QPushButton:checked {
                        background-color: #e0e0e0;
                        border: 1px solid #888;
                        border-radius: 2px;
                    }
                """)
                btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                btn.adjustSize()
                if subclass == student.subclass:
                    btn.setChecked(True)
                btn.clicked.connect(self.update_student_subclass(student, subclass))
                buttons.addButton(btn, col+1)
                self.grid.addWidget(btn, row, col)
            # buttons.buttons()[0].setChecked(True)

            name_edit = QLineEdit(name, self)
            # name_edit.setText(name)
            name_edit.textEdited.connect(self.update_student_name(student))
            self.grid.addWidget(name_edit, row, len(class_.subclasses))



    def update_student_name(self, student):
        def func(new_name):
            self.db.update_student_name(student, new_name)
        return func
    
    def update_student_subclass(self, student, subclass):
        def func():
            self.db.move_student(student, subclass)
        return func

