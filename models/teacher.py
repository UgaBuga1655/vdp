from db_config import Base, teacher_subject
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from itertools import pairwise

class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    av1 = Column(Integer)
    av2 = Column(Integer)
    av3 = Column(Integer)
    av4 = Column(Integer)
    av5 = Column(Integer)
    subjects = relationship("Subject", secondary=teacher_subject, back_populates="teachers")
    duties = relationship('TeacherDuty', back_populates='teacher')
    working_hours = Column(Integer, default=20)
    assign_duties = Column(Boolean, default=True)

    def __init__(self, name, av):
        self.name = name
        self.av1, self.av2, self.av3, self.av4, self.av5 = av 

    def days_available(self):
        return sum([1 for av in [self.av1, self.av2, self.av3, self.av4, self.av5 ] if av])

    @property
    def lessons(self):
        lessons = []
        for subject in self.subjects:
            lessons.extend(subject.lessons)
        return lessons

    def time_stats(self):
        blocks = [d.block for d in self.duties]
        duties_time = sum([b.length for b in blocks])
        lesson_time = 0
        for subject in self.subjects:
            for lesson in subject.lessons:
                if lesson.block is None:
                    continue
                blocks.append(lesson.block)
                lesson_time += lesson.block.length
        blocks.sort(key=lambda b: (b.day, b.start))
        breaks = 0
        for first, second in pairwise(blocks):
            if first.day != second.day:
                continue
            if second.start - first.start - first.length == 1:
                breaks += 1
        total = lesson_time + duties_time + breaks
        percetange = round(total / self.working_hours / 12 * 100, 1)
        return total, lesson_time, duties_time, breaks, percetange

