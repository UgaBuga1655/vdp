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

    def collision_text(self):
        return f'{self.teacher.name if self.teacher else "---"} ma dyżur w {self.classroom.name if self.classroom else "---"} ({self.block.print_time()})'
    
    def get_name(self):
        return f'{self.classroom.name if self.classroom else "---"}'
    
    def name_and_time(self):
        return f'Dyżur {self.teacher.name if self.teacher else "---"} w {self.classroom.name if self.classroom else "---"} ({self.block.print_time()})'