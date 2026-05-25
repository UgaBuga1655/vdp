from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QCheckBox, QHBoxLayout, QLabel, QPushButton, QGridLayout, QDoubleSpinBox
from PyQt5.QtCore import Qt
from data import Data
# from db_config import settings

class SettingsDialog(QWidget):
    def __init__(self, db: Data):
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

        stat_size = QHBoxLayout()
        stat_size.addWidget(QLabel('Statystyki pokoleń wstecz:'))
        self.stat_size = QSpinBox(minimum=0, maximum=1000, value=self.settings.stat_size)
        stat_size.addWidget(self.stat_size)
        main_layout.addLayout(stat_size)

        # pop size
        pop_size = QHBoxLayout()
        pop_size.addWidget(QLabel('Początkowa populacja:'))
        pop_size_spin = QSpinBox(minimum=0, maximum=100_000, value=self.settings.pop_size)
        pop_size.addWidget(pop_size_spin)
        pop_size_spin.valueChanged.connect(self.update_pop_size)
        main_layout.addLayout(pop_size)

        # # preserve popualtion
        # self.preserve_population = QCheckBox('Użyj ostatniej populacji')
        # self.preserve_population.setChecked(self.settings.preserve_population)
        # main_layout.addWidget(self.preserve_population)
        
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

        # parameters
        main_layout.addWidget(QLabel('Wagi parametrów oceniania:'))
        params = QGridLayout()
        for i, (name, value) in enumerate(zip(self.settings.scoring_names, self.settings.scoring_weights)):
            params.addWidget(QLabel(name + ':'), i, 0)
            spin = QDoubleSpinBox(value=value)
            spin.setSingleStep(0.1)
            spin.valueChanged.connect(self.update_param(i))
            params.addWidget(spin, i, 1)
        main_layout.addLayout(params)

        # max break
        max_break = QHBoxLayout()
        label = QLabel('Granica między przerwą a PW:')
        label.setToolTip('Jeśli czas między końcem a początkiem kolejnej lekcji jest krótszy lub równy, program bierze pod uwagę odległość między salami. Jeśli lekcje są tego samego przedmiotu, traktuje je jako odbywające się w bloku.')
        max_break.addWidget(label)
        self.max_break_spin = QSpinBox(value=self.settings.max_break*5, suffix=" min", maximum=60)
        self.max_break_spin.setSingleStep(5)
        self.max_break_spin.editingFinished.connect(self.update_max_break)
        max_break.addWidget(self.max_break_spin)
        main_layout.addLayout(max_break)


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
        self.params = self.settings.scoring_weights.copy()
        self.max_break = self.settings.max_break

    def update_verbose(self, value):
        self.verbose = value

    def update_generations(self, value):
        self.generations = value

    def update_pop_size(self, value):
        self.pop_size = value

    def update_cutoff(self, value):
        self.cutoff = value/100
    
    def update_param(self, i):
        def func(val):
            self.params[i] = val
        return func
    
    def update_max_break(self):
        val = self.max_break_spin.value()
        self.max_break = val//5
        self.max_break_spin.setValue(self.max_break*5)

    def apply(self):
        self.db.update_settings(
            verbose=self.verbose, 
            generations=self.generations,
            pop_size=self.pop_size,
            cutoff=self.cutoff,
            scoring_weights=self.params.copy(),
            max_break=self.max_break,
            preserve_population=self.preserve_population.isChecked(),
            stat_size=self.stat_size.value()
        )
        self.close()

        