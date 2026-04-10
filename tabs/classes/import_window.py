from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QSpinBox, QHBoxLayout, QLabel, QGridLayout, QDialogButtonBox

class ImportFormatWindow(QDialog):
    def __init__(self, parent, filename):
        super().__init__(parent=parent)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        grid = QGridLayout()
        main_layout.addLayout(grid)

        grid.addWidget(QLabel('Kolumny w których jest imię:'), 0, 0)
        self.n_of_name_cols = QSpinBox()
        self.n_of_name_cols.setMinimum(1)
        grid.addWidget(self.n_of_name_cols, 0, 1)

        grid.addWidget(QLabel('Liczba podklas:'), 1, 0)
        self.n_of_subclasses = QSpinBox()
        self.n_of_subclasses.setMinimum(1)
        grid.addWidget(self.n_of_subclasses, 1, 1)

        button_box = QDialogButtonBox( QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
