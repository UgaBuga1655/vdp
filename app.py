import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QAction, QMenu
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon

import shutil
import os
import sys
import multiprocess as mp

from data import Data
from tabs import Tabs
from functions import get_user_data_dir
from settings_dialog import SettingsDialog
from reports import RemainingLessonsWindow, TimeReport



user_data_dir = get_user_data_dir('VDP')
os.makedirs(user_data_dir, exist_ok=True)
db_name_path = os.path.join(user_data_dir, 'db_name')
basedir = os.path.dirname(__file__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.col_set = None


        if not os.path.isfile(db_name_path):
            with open(db_name_path, 'x') as f:
                pass
        
        with open(db_name_path, 'r+') as f:
            self.db_name = f.read().strip()
            if not self.db_name:
                self.db_name = os.path.join(user_data_dir, 'planer.vdp')
                f.write(self.db_name)

        self.db = Data(self.db_name)


        filename = self.db_name.split('/')[-1]
        self.setWindowTitle(f"VDP - {filename}")
        self.setWindowIcon(QIcon(os.path.join(basedir,'icon.png')))
        self.setMinimumSize(QSize(800, 800))
        self.tabs = Tabs(self)

        new_action = QAction('Nowy', self)
        new_action.triggered.connect(self.new_data)

        load_action = QAction('Wczytaj', self)
        load_action.triggered.connect(self.load_data)

        backup_action = QAction('Stwórz kopię zapasową', self)
        backup_action.triggered.connect(self.backup_data)

        export_action = QAction('&Eksportuj', self)
        export_action.triggered.connect(self.tabs.plan.export)
        

        menu = self.menuBar()
        file_menu = menu.addMenu('&Plik')
        file_menu.addActions([
            new_action,
            load_action,
            backup_action,
            export_action
        ])

        plan_menu = menu.addMenu('&Lekcje')
        clear_menu = plan_menu.addMenu('&Wyczyść')

        clear_unl_les_action = QAction('&Niezablokowane', self)
        clear_unl_les_action.triggered.connect(self.clear_unl_lessons)
        clear_all_les_action = QAction('&Wszystkie', self)
        clear_all_les_action.triggered.connect(self.clear_all_lessons)
        clear_menu.addActions([clear_unl_les_action, clear_all_les_action])

        lock_all_action = QAction('&Przypnij wszystkie', self)
        lock_all_action.triggered.connect(self.lock_all_lessons)
        unlock_all_action = QAction('&Odepnij wszystkie', self)
        unlock_all_action.triggered.connect(self.unlock_all_lessons)
        unlock_all_without_classroom = QAction('Odepnij nieprzypisane do sali', self)
        unlock_all_without_classroom.triggered.connect(self.unlock_all_lessons_without_classrooms)

        plan_menu.addActions([
            lock_all_action,
            unlock_all_action,
            unlock_all_without_classroom
        ])

        coloring_menu = menu.addMenu('&Uzupełnianie')
        color_lessons_action = QAction('&Uzupełnij plan', self)
        color_lessons_action.triggered.connect(self.color_lessons)
        settings_action = QAction('U&stawienia', self)
        settings_action.triggered.connect(self.coloring_settings)

        coloring_menu.addActions([
            color_lessons_action,
            settings_action
        ])

        reports_menu = menu.addMenu('&Raporty')
        remaining_action = QAction('&Pozostałe lekcje', self)
        remaining_action.triggered.connect(self.remaining_lessons_report)
        time_rep_action = QAction('&Czas w szkole', self)
        time_rep_action.triggered.connect(self.time_report)

        reports_menu.addActions([
            remaining_action,
            time_rep_action
        ])

        self.setCentralWidget(self.tabs)


    def load_data(self):
        db_name, _ = QFileDialog.getOpenFileName(self, 'Wczytaj dane', str(user_data_dir.absolute()), '*.vdp', '*.vdp')
        if not db_name:
            return
        self.db_name = db_name
        self.db = Data(self.db_name)
        self.tabs.load_data(self.db)
        with open(db_name_path, mode='w') as f:
            f.write(self.db_name)
        filename = self.db_name.split('/')[-1]
        self.setWindowTitle(f"VDP - {filename}")
        return True
    
    def backup_data(self):
        directory = os.path.join(user_data_dir, f'{self.db_name[:-4]} - kopia zapasowa.vdp')
        path, _ = QFileDialog.getSaveFileName(self, 'Stwórz kopię zapasową', directory, '*.vdp', '*.vdp')
        if not path:
            return
        shutil.copy(self.db_name, path)
        return True
    
    def new_data(self):
        directory = os.path.join(user_data_dir, 'planer.vdp')
        path, _ = QFileDialog.getSaveFileName(self, 'Stwórz kopię zapasową', directory, '*.vdp', '*.vdp')
        if not path:
            return
        self.db_name = path
        self.db = Data(self.db_name)
        self.tabs.load_data(self.db)
        with open(db_name_path, mode='w') as f:
            f.write(self.db_name)
        filename = self.db_name.split('/')[-1]
        self.setWindowTitle(f"VDP - {filename}")
        return True

    
    def clear_unl_lessons(self):
        self.db.clear_all_lesson_blocks(leave_locked=True)
        self.tabs.refresh()

    def clear_all_lessons(self):
        self.db.clear_all_lesson_blocks()
        self.tabs.refresh()

    def color_lessons(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.tabs.plan.color()
        # self.tabs.refresh()
        QApplication.restoreOverrideCursor()

    def lock_all_lessons(self):
        self.db.pin_all_lessons()
        # self.tabs.refresh()

    def unlock_all_lessons(self):
        self.db.pin_all_lessons(False)
        # self.tabs.refresh()

    def unlock_all_lessons_without_classrooms(self):
        self.db.pin_lessons_without_classrooms(False)

    def coloring_settings(self): 
        if self.col_set is None:
            self.col_set = SettingsDialog()
        self.col_set.show()

    def remaining_lessons_report(self):
        if not hasattr(self, 'rem_les_win') or self.rem_les_win is None:
            self.rem_les_win = RemainingLessonsWindow(self.db)
        self.rem_les_win.show()
        self.rem_les_win.load()

    def time_report(self):
        if not hasattr(self, 'time_report_win') or self.time_report_win is None:
            self.time_report_win = TimeReport(self.db)
        self.time_report_win.show()
        self.time_report_win.load()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    window.tabs.plan.view.set_ready()
    # window.tabs.plan.view.draw()
    app.exec()

if __name__ == '__main__':
    mp.freeze_support()
    main()