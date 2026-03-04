from data import Data, Lesson
from PyQt5.QtCore import QObject, pyqtSignal
from .none_stat import Statistic

class StudentDensityStat(Statistic):

    def __init__(self, db):
        super().__init__(db)
        self.stats = [[0]*8*12 for _ in range(5)]


    def load_stat(self):
        self.stats = [[0]*8*12 for _ in range(5)]
        lesson: Lesson
        for lesson in self.db.all_lessons():
            self.add_lesson(lesson)
        # print(self.stats)


    def add_lesson(self, lesson: Lesson):
        if lesson.block is None:
            return
        weight = len(lesson.subject.students)
        for five_min_block in range(int(lesson.length/5)):
            self.stats[lesson.block.day][lesson.block.start + five_min_block] += weight


    def remove_lesson(self, lesson: Lesson):
        if lesson.block is None:
            return
        weight = len(lesson.subject.students)
        for five_min_block in range(lesson.length):
            self.stats[lesson.day][lesson.block.start + five_min_block] -= weight

    def get_stats(self):
        return self.stats