from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.enums import DayOfWeek, TimePeriod

class SpeedRecordBase(BaseModel):
    timestamp: datetime
    speed: float
    day_of_week: DayOfWeek
    time_period: TimePeriod

class SpeedRecordResponse(SpeedRecordBase):
    id: int
    link_id: int

    model_config = ConfigDict(from_attributes=True)
