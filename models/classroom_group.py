
from db_config import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

class ClassroomGroup(Base):
    __tablename__ = 'classroom_groups'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    classrooms = relationship("Classroom", back_populates='group')