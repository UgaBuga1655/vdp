from PyQt5.QtWidgets import QLabel, QMenu, QAction, QInputDialog
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from data import Student

class NameLabel(QLabel):
    delete = pyqtSignal(Student)
    update_name = pyqtSignal(Student, str)


    def __init__(self, student):
        super().__init__(student.name)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.student = student
        self.customContextMenuRequested.connect(self.contextMenuEvent)


    def contextMenuEvent(self, event: QPoint):
        menu = QMenu(self)

        action_delete = QAction("Usuń", self)
        action_delete.triggered.connect(self.delete_student)

        action_edit = QAction("Edytuj", self)
        action_edit.triggered.connect(self.update_student_name)

        menu.addAction(action_edit)
        menu.addAction(action_delete)

        menu.exec_(self.mapToGlobal(event))

    def update_student_name(self):
        name, ok = QInputDialog.getText(self, 'Edytuj ucznia', 'Imię i nazwisko', text=self.text())
        if not ok:
            return
        # self.class_widget.db.update_student_name(self.student, name)
        self.update_name.emit(self.student, name)
        self.setText(name)

    def delete_student(self):
        self.delete.emit(self.student)
