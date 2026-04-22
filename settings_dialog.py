from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QCheckBox, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
# from db_config import settings

class SettingsDialog(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.settings = db.settings()
        self.setWindowFlags(Qt.Tool) 
        main_layout  = QVBoxLayout()
        self.setLayout(main_layout)
        self.setWindowTitle('Ustawienia uzupełniania')

        # verbose
        verbose = QCheckBox('Pokazuj graf')
        verbose.setChecked(self.settings.verbose)
        verbose.clicked.connect(self.update_verbose)
        main_layout.addWidget(verbose)

        # pop size
        pop_size = QHBoxLayout()
        pop_size.addWidget(QLabel('Początkowa populacja:'))
        pop_size_spin = QSpinBox(minimum=0, maximum=100_000, value=self.settings.pop_size)
        pop_size.addWidget(pop_size_spin)
        pop_size_spin.valueChanged.connect(self.update_pop_size)
        main_layout.addLayout(pop_size)

        # generations
        generations = QHBoxLayout()
        generations.addWidget(QLabel('Liczba pokoleń:'))
        gen_spin = QSpinBox(value=self.settings.generations)
        generations.addWidget(gen_spin)
        gen_spin.valueChanged.connect(self.update_generations)
        main_layout.addLayout(generations)

        # cutoff
        cutoff = QHBoxLayout()
        cutoff.addWidget(QLabel('Przeżywalność:'))
        cut_spin = QSpinBox(suffix='%', maximum=100, value=int(self.settings.cutoff*100))
        cut_spin.valueChanged.connect(self.update_cutoff)
        cutoff.addWidget(cut_spin)
        main_layout.addLayout(cutoff)

        btn_row = QHBoxLayout()
        main_layout.addLayout(btn_row)
        # apply
        apply_btn = QPushButton('Potwierdź')
        apply_btn.clicked.connect(self.apply)
        btn_row.addWidget(apply_btn)

        # cancel
        cancel_btn = QPushButton('Anuluj')
        cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(cancel_btn)

        self.verbose = self.settings.verbose
        self.generations = self.settings.generations
        self.pop_size = self.settings.pop_size
        self.cutoff = self.settings.cutoff

    def update_verbose(self, value):
        self.verbose = value

    def update_generations(self, value):
        self.generations = value

    def update_pop_size(self, value):
        self.pop_size = value

    def update_cutoff(self, value):
        self.cutoff = value/100

    def apply(self):
        self.db.update_settings(
            verbose=self.verbose, 
            generations=self.generations,
            pop_size=self.pop_size,
            cutoff=self.cutoff
        )
        self.close()

        