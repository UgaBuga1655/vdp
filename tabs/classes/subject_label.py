from PyQt5.QtWidgets import QLabel, QMenu, QAction, QVBoxLayout, QComboBox, QDialog, QDialogButtonBox
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from data import Subject, Class, Subclass

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
 
class SubjectLabel(QLabel):
    delete = pyqtSignal(Subject)
    edit = pyqtSignal(Subject)
    copy = pyqtSignal(Subject)

    def __init__(self, subject: Subject):
        name = subject.get_name(1,0,0) if subject else ''
        super().__init__(name)
        self.subject = subject
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        return QSize(size.height(), size.width())

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(size.height()+10, size.width()+15)
    

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



    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(0, self.height()-5)
        painter.rotate(275)
        painter.drawText(0, 0, self.height(), self.width(),
                         Qt.AlignLeft | Qt.AlignVCenter, self.text())
        
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
    