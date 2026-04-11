from PyQt5.QtWidgets import QDialog, QTabWidget, QDialogButtonBox, QVBoxLayout

from data import Subject, Data
from .import_students_widget import ImportStudentsWidget
from .import_subjects_widget import ImportSubjectsWidget

class ImportDialog(QDialog):
    def __init__(self, parent, students, subject_names, class_):
        super().__init__(parent)
        self.setWindowTitle(class_.name)
        self.setMinimumSize(800, 600)
        self.db: Data = parent.db
        self.students = students

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)


        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        self.students_tab = ImportStudentsWidget(self, students, class_)
        self.tabs.addTab(self.students_tab, 'Uczniowie')
        self.subjects_tab = ImportSubjectsWidget(self, subject_names, class_)
        self.tabs.addTab(self.subjects_tab, 'Przedmioty')

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        main_layout.addWidget(button_box)

    def accept(self):
        for name, subjects in self.students:
            student = self.students_tab.students[name]
            for subject_name in subjects:
                subject: Subject = self.subjects_tab.subjects[subject_name]
                self.db.add_subject_to_student(subject, student)
            self.db.move_student(student, student.subclass)
        return super().accept()

