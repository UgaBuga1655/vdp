from db_config import Base, subclass_customblock
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Subclass(Base):
    __tablename__ = 'subclasses'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'))
    students = relationship("Student", back_populates="subclass")
    subjects = relationship("Subject", back_populates="subclass")
    blocks = relationship("LessonBlockDB", back_populates="subclass")
    class_ = relationship('Class', back_populates='subclasses')
    custom_blocks = relationship("CustomBlock", secondary=subclass_customblock, back_populates="subclasses")

    def full_name(self):
        if len(self.class_.subclasses) == 1:
            return self.class_.name
        else:
            return self.class_.name + self.name
    
    def get_class(self):
        return self.class_
