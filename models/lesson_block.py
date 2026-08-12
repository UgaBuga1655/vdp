from .block import Block
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class LessonBlockDB(Block):
    __tablename__ = 'lesson_blocks'
    __mapper_args__ = {"polymorphic_identity": "lesson_block"}
    id = Column(ForeignKey("blocks.id"), primary_key=True)

    class_id = Column(Integer, ForeignKey('classes.id'))
    class_ = relationship("Class", back_populates='blocks')
    subclass_id = Column(Integer, ForeignKey('subclasses.id'))
    subclass = relationship("Subclass", back_populates='blocks')


    def parent(self):
        if self.class_:
            return self.class_
        if self.subclass:
            return self.subclass
        
    def print_full_time(self):
        return self.parent().full_name() + ' ' + super().print_full_time()