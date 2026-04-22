from db_config import Base
from sqlalchemy import Column, Integer, Boolean, Double




class Settings():
    def __init__(self):
        self.allow_creating_conflicts = False
        self.hide_empty_blocks = False
        self.draw_blocks_full_width = False
        self.draw_custom_blocks = True
        self.alpha = 255
        self.italicize_unlocked_lessons = True
        self.move_lessons_from = None
        self.swap_lessons_from = None

        self.verbose = True
        self.pop_size= 6000
        self.generations = 30
        self.cutoff = 0.25

class Metadata(Base):
    __tablename__ = 'metadata'
    id = Column(Integer, primary_key=True)

    allow_conflicts = Column(Boolean, default=False)
    hide_empty_blocks = Column(Boolean, default=False)
    draw_blocks_full_width = Column(Boolean, default=False)
    draw_custom_blocks = Column(Boolean, default=True)
    alpha = Column(Integer, default=255)

    verbose = Column(Boolean, default=True)
    pop_size = Column(Integer, default=6000)
    generations = Column(Integer, default=30)
    cutoff = Column(Double, default=0.25)

    def update(self, **kwargs):
        for name, value in kwargs.items():
            self.__setattr__(name, value)


    
