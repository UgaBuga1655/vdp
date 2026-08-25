from db_config import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    
    block_id = Column(Integer, ForeignKey('blocks.id'))
    block = relationship('Block', back_populates='events')

    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    teacher = relationship('Teacher', back_populates='duties')

    classroom_id = Column(Integer, ForeignKey('classrooms.id'))
    classroom = relationship('Classroom', back_populates='events')

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "event",
    }

    @property
    def students(self):
        return []

    @property
    def teachers(self):
        return [self.teacher] if self.teacher else []