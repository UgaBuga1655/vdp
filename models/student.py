from db_config import Base, student_subject
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from numpy import zeros
from .day_stat import DayStat

# time a break needs to last to be suitable for free work
min_free_work_time = 4 # *5=20 minutes

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'))
    subclass_id = Column(Integer, ForeignKey('subclasses.id'))
    subjects = relationship("Subject", secondary=student_subject, back_populates="students")

    def time_stats(self, only_day=None):
        days = [only_day] if only_day else range(5)
        matrix = zeros([5, 12*8])
        stats = [DayStat() for _ in range(5)]

        for subject in self.subjects:
            for lesson in subject.lessons:
                if not lesson.block or (only_day and lesson.block!=only_day):
                    continue
                day = lesson.block.day
                stats[day].time_in_lessons += lesson.length//5
                for n in range(lesson.length//5):
                    matrix[lesson.block.day, lesson.block.start+n] = 1

        for day in days:
            start_time = None
            end_time = None
            curr_break_time = 0
            free_work_time = 0
            for time, busy in enumerate(matrix[day,]):
                if busy:
                    end_time = time
                    if start_time is None:
                        start_time = time
                    if curr_break_time >= min_free_work_time:
                        free_work_time += curr_break_time
                    curr_break_time = 0
                else:
                    curr_break_time += 1
            free_work_time+=curr_break_time
            if start_time is None:
                stats[day].time_in_school = 0
            else:
                stats[day].time_in_school = end_time - start_time + 1
            stats[day].time_of_free_work = free_work_time - 12

        return stats
                        