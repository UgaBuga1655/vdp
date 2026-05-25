from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QComboBox, QVBoxLayout

class PopDialog(QDialog):
    def __init__(self, parent = ..., flags = ...):
        super().__init__(parent)
        self.setWindowTitle('Wybierz Tryb')

        main_layout = QVBoxLayout(self)
        self.choice = QComboBox()
        main_layout.addWidget(self.choice)

        
        if parent.db.pop_exists():
            self.choice.addItem('Kontynuuj uzupełnianie', 'continue')
        self.choice.addItem('Zacznij od początku', 'new')
        self.choice.addItem('Dopracuj obecny plan', 'edit_current')

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

