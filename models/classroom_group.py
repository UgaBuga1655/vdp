from db_config import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

class ClassroomGroup(Base):
    __tablename__ = 'classroom_groups'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    classrooms = relationship("Classroom", back_populates='group')
    distances_from = relationship('Distance', back_populates='start', foreign_keys='Distance.start_id')
    distances_to = relationship('Distance', back_populates='end', foreign_keys='Distance.end_id')