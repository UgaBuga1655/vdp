from db_config import Base, student_subject, settings
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class TeacherDuty(Base):
    __tablename__= 'teacher_duties'
    id = Column(Integer, primary_key=True)

    block_id = Column(Integer, ForeignKey('custom_blocks.id'))
    block = relationship('CustomBlock', back_populates='duties')

    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    teacher = relationship('Teacher', back_populates='duties')
    
    classroom_id = Column(Integer, ForeignKey('classrooms.id'))
    classroom = relationship('Classroom', back_populates='duties')

    def collision_text(self):
        return f'{self.teacher.name} ma dyżur w {self.classroom.name} ({self.block.print_time()})'
    
    def get_name(self):
        return f'{self.classroom.name}'