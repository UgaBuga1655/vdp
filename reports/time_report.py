from ast import main
from re import sub
from sqlite3 import DatabaseError

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QPushButton, QTableWidget ,QHBoxLayout, QComboBox, QTableWidgetItem
from PyQt5.QtCore import QSize, Qt, QPoint
from PyQt5.QtGui import QCursor
from data import Data
from models import DayStat
from functions import display_hour

class TimeReport(QWidget):
    def __init__(self, db: Data):
        super().__init__()
        self.setWindowFlag(Qt.Tool)
        self.db = db
        self.stats={}
        self.setMinimumSize(QSize(300, 400))
        self.setWindowTitle('Czas w szkole')
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        top_row = QHBoxLayout()
        main_layout.addLayout(top_row)
        self.group_select = QComboBox()
        top_row.addWidget(self.group_select)
        self.person_select = QComboBox()
        top_row.addWidget(self.person_select)
        # scroll_area = QScrollArea(self)
        # scroll_area.setWidget(self.tree)
        # self.layout().addWidget(scroll_area)
        self.table = QTableWidget()
        main_layout.addWidget(self.table)
        self.table.setRowCount(5)
        self.table.setColumnCount(6)
        self.table.setItem(0,1,QTableWidgetItem('Poniedziałek'))
        self.table.setItem(0,2,QTableWidgetItem('Wtorek'))
        self.table.setItem(0,3,QTableWidgetItem('Środa'))
        self.table.setItem(0,4,QTableWidgetItem('Czwartek'))
        self.table.setItem(0,5,QTableWidgetItem('Piątek'))

        self.table.setItem(1, 0, QTableWidgetItem('Od początku do końca lekcji'))
        self.table.setItem(2, 0, QTableWidgetItem('Lekcje'))
        self.table.setItem(3, 0, QTableWidgetItem('Praca własna'))
        self.table.setItem(4, 0, QTableWidgetItem('Praca własna między lekcjami'))

        refresh_btn = QPushButton('Odśwież')
        refresh_btn.clicked.connect(self.load)
        self.layout().addWidget(refresh_btn)

        self.group_select.currentIndexChanged.connect(self.load_students)
        self.person_select.currentIndexChanged.connect(self.present_stat)
        
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.move(QCursor.pos() + QPoint(10,10))

    def populate_table(self, stats):
        stat: DayStat
        for day, stat in enumerate(stats):
            self.table.setItem(1,day+1, QTableWidgetItem(display_hour(stat.time_in_school, as_absolute=False)))
            self.table.setItem(2,day+1, QTableWidgetItem(display_hour(stat.time_in_lessons, as_absolute=False)))
            self.table.setItem(3,day+1, QTableWidgetItem(display_hour(stat.free_work_time, as_absolute=False)))
            self.table.setItem(4,day+1, QTableWidgetItem(display_hour(stat.free_work_time_between_lessons, as_absolute=False)))


    def load(self):
        self.group_select.blockSignals(True)
        self.group_select.clear()
        self.group_select.addItem('Wszyscy uczniowie', None)
        total_students = 0
        self.stats = {}
        self.stats['total'] = [DayStat() for _ in range(5)]
        for subclass in self.db.all_subclasses():
            self.group_select.addItem(subclass.full_name(), subclass)
            n_of_students = len(subclass.students)
            total_students += n_of_students
            subclass_stats =  [DayStat() for _ in range(5)]
            self.stats[subclass] = subclass_stats
            for student in subclass.students:
                stat = student.time_stats()
                self.stats[student] = stat
                for n in range(5):
                    self.stats['total'][n]+=stat[n]
                    subclass_stats[n]+=stat[n]
            for stat in subclass_stats:
                stat/=n_of_students
        for stat in self.stats['total']:
            stat/=total_students
        self.group_select.blockSignals(False)
        self.load_students()

    def present_stat(self):
        stats = self.person_select.currentData()
        self.populate_table(stats)

    def load_students(self):
        self.person_select.blockSignals(True)
        self.person_select.clear()
        subclass = self.group_select.currentData()
        if not subclass:
            self.person_select.addItem('Średnia', self.stats['total'])
            self.present_stat()
            return
        self.person_select.addItem('Średnia', self.stats[subclass])
        for student in subclass.students:
            self.person_select.addItem(student.name, self.stats[student])
        self.person_select.blockSignals(False)
        self.present_stat()
        







        
