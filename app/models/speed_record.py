from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.schemas.enums import DayOfWeek, TimePeriod

class SpeedRecord(Base):
    __tablename__ = 'speed_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(Integer, ForeignKey('links.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    speed = Column(Float, nullable=False)
    
    # Store directly as string enums. We use values_callable so SQLAlchemy uses the string values ('Monday', 'AM Peak') instead of the variable names ('MONDAY', 'AM_PEAK')
    day_of_week = Column(SQLEnum(DayOfWeek, native_enum=False, length=15, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    time_period = Column(SQLEnum(TimePeriod, native_enum=False, length=20, values_callable=lambda obj: [e.value for e in obj]), nullable=False)

    link = relationship("Link", back_populates="speeds")

# Index that helps mostly with get_aggregate_speeds and get_slow_links
Index('idx_speed_link_day_period', SpeedRecord.link_id, SpeedRecord.day_of_week, SpeedRecord.time_period)