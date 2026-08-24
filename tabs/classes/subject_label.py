from PyQt5.QtWidgets import QMenu, QAction, QVBoxLayout, QComboBox, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt, pyqtSignal
from data import Subject
from vertical_label import VerticalLabel

class CopySubjectsDialog(QDialog):
    def __init__(self, parent, targets):
        super().__init__(parent=parent)
        self.setWindowTitle('Kopiuj Przedmiot')
        layout = QVBoxLayout(self)
        self.target_list = QComboBox()
        layout.addWidget(self.target_list)
        for target in targets:
            self.target_list.addItem(target.full_name(), target)
        buttonBox = QDialogButtonBox()
        layout.addWidget(buttonBox)
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
 
class SubjectLabel(VerticalLabel):
    delete = pyqtSignal(Subject)
    edit = pyqtSignal(Subject)
    copy = pyqtSignal(Subject)
    move_subject = pyqtSignal(Subject)

    def __init__(self, subject: Subject):
        name = subject.get_name(1,0,0) if subject else ''
        super().__init__(name)
        if len(subject.teachers):
            self.setToolTip('\n'.join([t.name for t in subject.teachers]))
        self.subject = subject
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)


    def contextMenuEvent(self, ev):
        menu = QMenu(self)

        action_edit = QAction("Edytuj", self)
        action_edit.triggered.connect(lambda: self.edit.emit(self.subject))
        menu.addAction(action_edit)

        action_copy = QAction('Kopiuj', self)
        action_copy.triggered.connect(lambda: self.copy.emit(self.subject))
        menu.addAction(action_copy)

        if self.subject.subclass:

            action_move = QAction('Przenieś do wspólnych', self)
            action_move.triggered.connect(lambda: self.move_subject.emit(self.subject))
            menu.addAction(action_move)

        action_delete = QAction("Usuń", self)
        action_delete.triggered.connect(lambda: self.delete.emit(self.subject))
        menu.addAction(action_delete)

        menu.exec_(self.mapToGlobal(ev))
    