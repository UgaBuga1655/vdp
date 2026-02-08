from PyQt5.QtWidgets import QLabel, QMenu, QAction
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QSize
from .subjects import SubjectsWidget

class VerticalLabel(QLabel):
    def __init__(self, db, subject, parent):
        name = subject.get_name(0,0,0) if subject else ''
        super().__init__(name, parent)

        self.db = db
        self.subject = subject
        self.class_widget = parent
                # self.setMargin(10)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        return QSize(size.height(), size.width())

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(size.height()+10, size.width()+10)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(0, self.height()-5)
        painter.rotate(275)
        painter.drawText(0, 0, self.height(), self.width(),
                         Qt.AlignLeft | Qt.AlignVCenter, self.text())
        
    def contextMenuEvent(self, ev):
        menu = QMenu(self)

        action_delete = QAction("Usuń", self)
        action_delete.triggered.connect(self.class_widget.delete_subject(self.subject))

        action_edit = QAction("Edytuj", self)
        action_edit.triggered.connect(self.edit)

        menu.addAction(action_edit)
        menu.addAction(action_delete)

        menu.exec_(self.mapToGlobal(ev))
        
    def edit(self, ev):
        if not self.subject:
            return
        dialog = SubjectsWidget(self, self.db, self.subject)
        ok = dialog.exec()