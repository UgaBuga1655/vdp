from turtle import back

from db_config import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, CheckConstraint
from sqlalchemy.orm import relationship

class Classroom(Base):
    __tablename__ = 'classrooms'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    subjects = relationship("Subject", back_populates="required_classroom")
    events = relationship('Event', back_populates='classroom')
    allow_lessons = Column(String, default='all') # 'all' / 'selected' / 'none'

    group_id = Column(Integer, ForeignKey('classroom_groups.id'))
    group = relationship('ClassroomGroup', back_populates='classrooms')