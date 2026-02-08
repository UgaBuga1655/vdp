from PyQt5.QtWidgets import QLabel, QMenu, QAction
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from data import Subject

class VerticalLabel(QLabel):
    delete = pyqtSignal(Subject)
    edit = pyqtSignal(Subject)

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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(0, self.height()-5)
        painter.rotate(275)
        painter.drawText(0, 0, self.height(), self.width(),
                         Qt.AlignLeft | Qt.AlignVCenter, self.text())
        
    def contextMenuEvent(self, ev):
        menu = QMenu(self)

        action_delete = QAction("Usuń", self)
        action_delete.triggered.connect(lambda: self.delete.emit(self.subject))

        action_edit = QAction("Edytuj", self)
        action_edit.triggered.connect(lambda: self.edit.emit(self.subject))

        menu.addAction(action_edit)
        menu.addAction(action_delete)

        menu.exec_(self.mapToGlobal(ev))
        
    # def edit(self, ev):
    #     if not self.subject:
    #         return
    #     dialog = SubjectsWidget(self, self.db, self.subject)
    #     ok = dialog.exec()