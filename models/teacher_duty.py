from db_config import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .event import Event

class TeacherDuty(Event):
    __tablename__= 'teacher_duties'
    __mapper_args__ = {"polymorphic_identity": "teacher_duty"}

    id = Column(ForeignKey("events.id"), primary_key=True)
    teacher_pinned = Column(Boolean, default=False)
    classroom_pinned = Column(Boolean, default=False)
    student_id = Column(Integer, ForeignKey('students.id'), default=None)
    student = relationship('Student', back_populates='duties')

    def collision_text(self, teacher_name=None):
        if teacher_name is None:
            teacher_name = self.teacher.name
        return f'{self.teacher.name if self.teacher else "---"} ma dyżur w {self.classroom.name if self.classroom else "---"} ({self.block.print_time()})'
    
    def get_name(self):
        return f'{self.classroom.name if self.classroom else "---"}'
    
    def name_and_time(self):
        return f'Dyżur {self.teacher.name if self.teacher else "---"} w {self.classroom.name if self.classroom else "---"} ({self.block.print_time()})'