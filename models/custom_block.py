from db_config import Base, days, subclass_customblock
from .block import Block
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from functions import display_hour

class CustomBlock(Block):
    __tablename__ = 'custom_blocks'
    __mapper_args__ = {"polymorphic_identity": "custom_block"}

    id = Column(ForeignKey("blocks.id"), primary_key=True)
    subclasses = relationship("Subclass", secondary=subclass_customblock, back_populates="custom_blocks")