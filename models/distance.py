from turtle import distance

from db_config import Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class Distance(Base):
    __tablename__ = 'distances'
    id = Column(Integer, primary_key=True)
    start_id = Column(Integer, ForeignKey('classroom_groups.id'))
    start = relationship('ClassroomGroup', back_populates='distances_from', foreign_keys=[start_id])
    end_id = Column(Integer, ForeignKey('classroom_groups.id'))
    end = relationship('ClassroomGroup', back_populates='distances_to', foreign_keys=[end_id])
    distance = Column(Integer, nullable=False)

