from PyQt5.QtWidgets import QLabel, QMenu, QAction
from PyQt5.QtCore import Qt, QPoint

class NameLabel(QLabel):
    def __init__(self, student, parent=None):
        super().__init__(student.name)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.student = student
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.class_wiget = parent

        # print(student.name)

    def contextMenuEvent(self, event: QPoint):
        menu = QMenu(self)

        action_delete = QAction("Usuń", self)
        action_delete.triggered.connect(self.class_wiget.delete_student(self.student))

        action_edit = QAction("Edit", self)
        action_edit.triggered.connect(lambda: print("Edit clicked"))

        # menu.addAction(action_edit)
        menu.addAction(action_delete)

        menu.exec_(self.mapToGlobal(event))
