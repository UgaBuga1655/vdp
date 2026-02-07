from PyQt5.QtWidgets import QLabel, QMenu, QAction, QInputDialog
from PyQt5.QtCore import Qt, QPoint

class NameLabel(QLabel):
    def __init__(self, student, parent=None):
        super().__init__(student.name)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.student = student
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.class_widget = parent

        # print(student.name)

    def contextMenuEvent(self, event: QPoint):
        menu = QMenu(self)

        action_delete = QAction("Usuń", self)
        action_delete.triggered.connect(self.class_widget.delete_student(self.student))

        action_edit = QAction("Edytuj", self)
        action_edit.triggered.connect(self.update_name)

        menu.addAction(action_edit)
        menu.addAction(action_delete)

        menu.exec_(self.mapToGlobal(event))

    def update_name(self):
        name, ok = QInputDialog.getText(self, 'Edytuj ucznia', 'Imię i nazwisko', text=self.text())
        if not ok:
            return
        self.class_widget.db.update_student_name(self.student, name)
        self.setText(name)
