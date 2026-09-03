from db_config import Base, student_subject, student_block
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
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
    class_ = relationship('Class', back_populates='students')
    subclass = relationship('Subclass', back_populates='students')
    duties = relationship("TeacherDuty", back_populates="student")
    non_mandatory_blocks = relationship('Block', secondary=student_block, back_populates='exempt_students')
    sen = Column(Boolean, default=False)

    def target_5_min_slots_in_school(self):
        time = 0
        n_of_lessons = 0
        for subject in self.subjects:
            for lesson in subject.lessons:
                n_of_lessons += lesson.length // 30
        time = n_of_lessons * 45
        time += 425
        # print(time)
        time //= 5
        # print(time)
        return time
        

    def time_stats(self, only_day=None):
        days = [only_day] if only_day else range(5)
        matrix = zeros([5, 12*8])
        stats = [DayStat() for _ in range(6)]

        for subject in self.subjects:
            for lesson in subject.lessons:
                if not lesson.block or (only_day and lesson.block!=only_day):
                    continue
                day = lesson.block.day
                stats[day].time_in_lessons += lesson.length//5
                stats[-1].time_in_lessons += lesson.length//5
                for n in range(lesson.length//5):
                    matrix[lesson.block.day, lesson.block.start+n] = 1

        for day in days:
            start_time = None
            end_time = None
            curr_break_time = 0
            free_work_time = 0
            time_before_lessons = 0
            for time, busy in enumerate(matrix[day,]):
                if busy:
                    end_time = time
                    if start_time is None:
                        start_time = time
                        time_before_lessons = curr_break_time
                    if curr_break_time >= min_free_work_time:
                        free_work_time += curr_break_time
                    curr_break_time = 0
                else:
                    curr_break_time += 1
            free_work_between_lessons = free_work_time - time_before_lessons
            free_work_time+=curr_break_time
            if start_time is None:
                stats[day].time_in_school = 0
            else:
                stats[day].time_in_school = end_time - start_time + 1
                stats[-1].time_in_school += end_time - start_time +1
            stats[day].free_work_time = free_work_time - 12
            stats[-1].free_work_time += free_work_time - 12
            stats[day].free_work_time_between_lessons = free_work_between_lessons
            stats[-1].free_work_time_between_lessons += free_work_between_lessons

        return stats
                        