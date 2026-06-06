from .block import Block
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class LessonBlockDB(Block):
    __tablename__ = 'lesson_blocks'
    id = Column(ForeignKey("blocks.id"), primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'))
    subclass_id = Column(Integer, ForeignKey('subclasses.id'))
    lessons = relationship("Lesson", backref="block")
    class_ = relationship("Class", back_populates='blocks')
    subclass = relationship("Subclass", back_populates='blocks')
    __mapper_args__ = {"polymorphic_identity": "lesson_block"}
    def parent(self):
        if self.class_:
            return self.class_
        if self.subclass:
            return self.subclass