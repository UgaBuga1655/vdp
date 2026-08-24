from db_config import Base
from sqlalchemy import Column, PickleType, Integer

class Results(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    best_result = Column(PickleType)
    population = Column(PickleType)
    bl_g = Column(PickleType)
    for_bl = Column(PickleType)
    les_g = Column(PickleType)
    feas = Column(PickleType)
    inconv = Column(PickleType)
    best_params = Column(PickleType)
    all_params = Column(PickleType)
    stats = Column(PickleType)

    def update(self, **kwargs):
        for name, value in kwargs.items():
            self.__setattr__(name, value)
    