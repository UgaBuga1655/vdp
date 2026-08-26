from db_config import Base, student_subject, teacher_subject
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    short_name = Column(String)
    class_id = Column(Integer, ForeignKey('classes.id'))
    class_ = relationship('Class', back_populates='subjects')
    subclass_id = Column(Integer, ForeignKey('subclasses.id'))
    subclass = relationship('Subclass', back_populates='subjects')
    # teacher_id = Column(Integer, ForeignKey('teachers.id'))
    # teacher = relationship('Teacher', backref='subjects_old')
    teachers = relationship('Teacher', secondary=teacher_subject, back_populates='subjects')
    classroom_id = Column(Integer, ForeignKey('classrooms.id'))
    required_classroom = relationship('Classroom', back_populates='subjects')
    basic = Column(Boolean)
    is_a_project = Column(Boolean, default=False)
    color = Column(String)
    target_block_length = Column(Integer, default=1)
    students = relationship("Student", secondary=student_subject, back_populates="subjects")
    lessons = relationship("Lesson", back_populates="subject")

    for1 = Column(Integer, default=0)
    for2 = Column(Integer, default=0)
    for3 = Column(Integer, default=0)
    for4 = Column(Integer, default=0)
    for5 = Column(Integer, default=0)

    inconv1 = Column(Integer, default=0)
    inconv2 = Column(Integer, default=0)
    inconv3 = Column(Integer, default=0)
    inconv4 = Column(Integer, default=0)
    inconv5 = Column(Integer, default=0)

    def parent(self):
        if self.class_:
            return self.class_
        if self.subclass:
            return self.subclass
        
    def absolute_class(self):
        return self.class_ if self.class_ else self.subclass.class_
        
    def class_name(self):
        # return(f'{self.class_id}, {self.subclass_id}')
        return self.class_.name if self.class_id is not None else self.subclass.class_.name

    def get_name(self):
        return self.name + '' if self.basic else ' R'
    
    def get_short_name(self):
        return self.short_name + '' if self.basic else ' R'
        
    # def full_name(self, full_subclass_name = False):
    #     if self.my_class:
    #         return f'{self.name} {self.my_class.name if settings.draw_blocks_full_width else ""} R'
    #     else:
    #         return f'{self.name} {self.subclass.full_name() if full_subclass_name or settings.draw_blocks_full_width else self.subclass.name.upper()}'
    
    # def short_full_name(self, full_subclass_name = False):
    #     if self.my_class:
    #         return self.short_name + ' R'
    #     else:
    #         return f'{self.short_name} {self.subclass.full_name() if full_subclass_name or settings.draw_blocks_full_width else self.subclass.name.upper()}'
        
    def get_name(self, short=False, show_class_name = True, show_subclass_name = True):
        name = self.short_name if short else self.name
        if not name:
            name = ''
       
        class_name = ''
        if show_class_name:
            class_name += self.class_name()
        is_only_subclass = len(self.class_.subclasses if self.class_ else self.subclass.class_.subclasses) == 1
        if show_subclass_name:
            class_name +=  (self.subclass.name.upper() if (not is_only_subclass and self.subclass) else '') if self.basic else ''
               
        if not self.basic:
            class_name += 'R'
        if class_name:
            name += ' ' + class_name

        return name
        
        
    

