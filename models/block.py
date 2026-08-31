from db_config import Base, days
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from functions import display_hour

class Block(Base):
    __tablename__ = 'blocks'
    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    length = Column(Integer, nullable=False) # in 5 min blocks
    start = Column(Integer, nullable=False) # in 5 min blocks
    day = Column(Integer, nullable=False) # 0=mon, 1=tue etc.
    color = Column(String, default='#c0c0c0')
    text = Column(String)
    events = relationship('Event', back_populates='block')

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "block",
    }
    
        
    def print_time(self):
        return f'{display_hour(self.start)}-{display_hour(self.start+self.length)}'
    
    def __str__(self):
        return self.print_full_time()
    
    def print_full_time(self):
        return f'{days[self.day]} {self.print_time()}'

    @property
    def duties(self):
        return [ev for ev in self.events if ev.type == 'teacher_duty']
   