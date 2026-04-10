from db_config import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
import csv

class Class(Base):
    __tablename__ = 'classes'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    students = relationship("Student", backref="my_class")
    subclasses = relationship("Subclass", backref="my_class")
    subjects = relationship("Subject", backref="my_class")
    blocks = relationship("LessonBlockDB", backref="my_class")
    order = Column(Integer)

    def full_name(self):
        return self.name
    
    
    def to_csv(self, filename):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|')
            for student in self.students:
                writer.writerow([student.name] + [subject.get_name(show_subclass_name=True) for subject in student.subjects])