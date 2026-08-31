from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from vertical_label import VerticalLabel
from functions import display_hour
from data import Teacher, Data

class TeacherReport(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db: Data = db
        self.setWindowTitle('Czas pracy nauczycieli')
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.container = QWidget()
        btn = QPushButton('Odśwież')
        btn.clicked.connect(self.load)
        self.main_layout.addWidget(btn)
        print('foo')

    def load(self):
        self.container.deleteLater()
        self.container = QWidget()
        self.main_layout.insertWidget(0, self.container)
        grid = QGridLayout()
        self.container.setLayout(grid)
        grid.addWidget(VerticalLabel('Lekcje'), 0, 1)
        grid.addWidget(VerticalLabel('Dyżury'), 0, 2)
        grid.addWidget(VerticalLabel('Przerwy'), 0, 3)
        grid.addWidget(VerticalLabel('Łącznie'), 0, 4)
        grid.addWidget(VerticalLabel('%'), 0, 5)
        grid.addWidget(VerticalLabel('Maksymalny'), 0, 6)

        for row, teacher in enumerate(self.db.all_teachers()):
            grid.addWidget(QLabel(teacher.name), row+1, 0)
            
            total, lesson_time, duties_time, breaks, percetange = teacher.time_stats()
            grid.addWidget(QLabel(display_hour(lesson_time, False)), row+1, 1)
            grid.addWidget(QLabel(display_hour(duties_time, False)), row+1, 2)
            grid.addWidget(QLabel(display_hour(breaks, False)), row+1, 3)
            grid.addWidget(QLabel(display_hour(total, False)), row+1, 4)
            grid.addWidget(QLabel(f'{round(percetange,1)}%'), row+1, 5)
            grid.addWidget(QLabel(f'{teacher.working_hours}:00'), row+1, 6)

