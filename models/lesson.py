from db_config import Base
from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .event import Event

class Lesson(Event):
    __tablename__ = 'lessons'
    __mapper_args__ = {"polymorphic_identity": "lesson"}
    id = Column(ForeignKey("events.id"), primary_key=True)
    length = Column(Integer, nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    subject = relationship('Subject', back_populates='lessons')
    # classroom_id = Column(Integer, ForeignKey('classrooms.id'))
    block_locked = Column(Boolean, default=False)
    classroom_locked = Column(Boolean)

    def name_and_time(self):
        return f'{self.subject.get_name()} o {self.block.print_time() if self.block else "(nieprzypisany)"}'

    def get_name(self):
        return self.subject.get_name()
    
    @property
    def teachers(self):
        return self.subject.teachers

    @property
    def teacher_names(self):
        if len(self.teachers) == 1:
            return self.teachers[0].name
        if len(self.teachers) == 2:
            return ' i '.join([t.name for t in self.teachers])
        return ', '.join([t.name for t in self.teachers[:-1]]) + ' i ' + self.teachers[-1].name
    
    @property
    def students(self):
        return self.subject.students
    
    def collision_text(self, teacher_name=None):
        if teacher_name is None:
            self.teacher_name = self.teacher_names
        return f'{teacher_name} prowadzi {self.name_and_time()}'

