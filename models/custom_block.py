from db_config import Base, days, subclass_customblock
from .block import Block
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from functions import display_hour

class CustomBlock(Block):
    __tablename__ = 'custom_blocks'
    id = Column(ForeignKey("blocks.id"), primary_key=True)
    subclasses = relationship("Subclass", secondary=subclass_customblock, back_populates="custom_blocks")
    # duties = relationship('TeacherDuty', back_populates='block')

    __mapper_args__ = {"polymorphic_identity": "custom_block"}
    # def parent(self):
    #     if self.my_class:
    #         return self.my_class
    #     if self.subclass:
    #         return self.subclass
        
    def print_time(self):
        return f'{display_hour(self.start)}-{display_hour(self.start+self.length)}'
    
   

    def print_full_time(self):
        return f'{days[self.day]} {self.print_time()}'

