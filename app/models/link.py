from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import Base

class Link(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    road_name = Column(String, index=True)
    length = Column(Float)
    
    geometry = Column(Geometry(geometry_type='LINESTRING', srid=4326, spatial_index=True))

    speeds = relationship("SpeedRecord", back_populates="link", cascade="all, delete-orphan")
