from PyQt5.QtWidgets import QLabel, QMenu, QAction, QInputDialog, QWidget, QHBoxLayout, QLineEdit, QSizePolicy
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from data import Student, Subclass

class NameLabel(QWidget):
    delete = pyqtSignal(Student)
    update_name = pyqtSignal(Student, str)
    move_student = pyqtSignal(Student, Subclass)


    def __init__(self, student: Student):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.row = QHBoxLayout()
        self.row.setContentsMargins(0,0,0,0)
        self.setLayout(self.row)
        self.label = QLabel(student.name)
        self.row.addWidget(self.label)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.student = student
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.edit = QLineEdit()
        self.edit.editingFinished.connect(self.update_student_name)
        self.row.addWidget(self.edit)
        self.edit.hide()


    def contextMenuEvent(self, event: QPoint):
        menu = QMenu(self)

        action_edit = QAction("Edytuj", self)
        action_edit.triggered.connect(self.edit_student_name)
        menu.addAction(action_edit)

        n_of_subclasses = len(self.student.class_.subclasses)
        if n_of_subclasses <= 2:
            move_menu = menu
            text = "Przenieś do "
        else:
            move_menu = menu.addMenu('Przenieś do')
            text = ''
        for subclass  in self.student.class_.subclasses:
            if subclass == self.student.subclass:
                continue
            action = QAction(text + subclass.name.upper(), self)
            action.triggered.connect(self.move_student_func(self.student, subclass))
            move_menu.addAction(action)

        action_delete = QAction("Usuń", self)
        action_delete.triggered.connect(self.delete_student)
        menu.addAction(action_delete)

        menu.exec_(self.mapToGlobal(event))

    def edit_student_name(self):
        self.label.hide()
        self.edit.setText(self.student.name)
        self.edit.setFocus()
        self.edit.selectAll()
        self.edit.blockSignals(False)
        self.edit.show()
        # name, ok = QInputDialog.getText(self, 'Edytuj ucznia', 'Imię i nazwisko', text=self.text())
        # if not ok:
            # return
        # self.class_widget.db.update_student_name(self.student, name)

    def update_student_name(self):
        new_name = self.edit.text()
        self.edit.blockSignals(True)
        self.edit.hide()
        self.label.show()
        if new_name == self.student.name:
            return
        self.update_name.emit(self.student, new_name)

    def delete_student(self):
        self.delete.emit(self.student)

    def move_student_func(self, student, subclass):
        def func():
            self.move_student.emit(student, subclass)
        return func
