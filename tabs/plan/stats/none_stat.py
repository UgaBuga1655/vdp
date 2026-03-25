from data import Data
from PyQt5.QtCore import QObject, pyqtSignal

class Statistic(QObject):
    def __init__(self, db: Data):
        super().__init__()
        self.db =db
        self.rects = [[]] * 5

    
    def load_stat(self):
        pass

    def add_lesson(self, lesson):
        pass

    def remove_lesson(self, lesson):
        pass

    def get_stats(self, only_day=None):
        return None