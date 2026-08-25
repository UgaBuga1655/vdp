from PyQt5.QtWidgets import QProgressBar, QWidget, QLabel, QVBoxLayout, QDialog
from PyQt5.QtCore import Qt

class ProgressDialog(QDialog):
    def __init__(self, title, total):
        super().__init__()
        self.setModal(True)
        self.setWindowFlag(Qt.Tool)
        self.setMinimumWidth(300)
        self.curr = 0
        self.total = total
        self.setWindowTitle(title)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label = QLabel()
        layout.addWidget(self.label)
        self.bar = QProgressBar()
        layout.addWidget(self.bar)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def set_label(self, label):
        self.show()
        self.label.setText(label)

    def set_total(self, total):
        self.total = total
        self.curr = 0
        self.bar.setValue(0)

    def next(self, n=1):
        if not n:
            return
        self.curr += n
        if self.total:
            self.bar.setValue(int(self.curr/self.total*100))
        else: 
            self.bar.setValue(100)

    def set(self, n):
        self.bar.setValue(int(n/self.total*100))