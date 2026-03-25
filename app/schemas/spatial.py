from pydantic import BaseModel, model_validator
from typing import Optional
from app.schemas.enums import DayOfWeek, TimePeriod

class SpatialFilter(BaseModel):
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    day: Optional[DayOfWeek] = None
    period: Optional[TimePeriod] = None

    @model_validator(mode="after")
    def validate_bbox(self):
        if self.min_lon >= self.max_lon:
            raise ValueError("min_lon must be less than max_lon")
        if self.min_lat >= self.max_lat:
            raise ValueError("min_lat must be less than max_lat")
        return self