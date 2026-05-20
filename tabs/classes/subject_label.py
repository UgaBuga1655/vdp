from PyQt5.QtWidgets import QMenu, QAction, QVBoxLayout, QComboBox, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt, pyqtSignal
from data import Subject
from vertical_label import VerticalLabel

class CopySubjectsDialog(QDialog):
    def __init__(self, parent, targets):
        super().__init__(parent=parent)
        self.setWindowTitle('Kopiuj Lekcje')
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

    def __init__(self, subject: Subject):
        name = subject.get_name(1,0,0) if subject else ''
        super().__init__(name)
        if subject.teacher_id:
            self.setToolTip(subject.teacher.name)
        self.subject = subject
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
    def copy_subjects(self):
        if self.subject.subclass:
            targets = self.db.all_subclasses()
        else:
            targets = self.db.all_classes()
        dialog = CopySubjectsDialog(self, targets)
        ok = dialog.exec()
        if not ok:
            return
        target = dialog.target_list.currentData()
        self.copy.emit(self.subject, target)

    def contextMenuEvent(self, ev):
        menu = QMenu(self)

        action_edit = QAction("Edytuj", self)
        action_edit.triggered.connect(lambda: self.edit.emit(self.subject))
        menu.addAction(action_edit)

        action_copy = QAction('Kopiuj', self)
        action_copy.triggered.connect(lambda: self.copy.emit(self.subject))
        menu.addAction(action_copy)

        action_delete = QAction("Usuń", self)
        action_delete.triggered.connect(lambda: self.delete.emit(self.subject))
        menu.addAction(action_delete)

        menu.exec_(self.mapToGlobal(ev))
    