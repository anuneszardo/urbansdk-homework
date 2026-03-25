from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from app.schemas.speed_record import SpeedRecordResponse

class LinkBase(BaseModel):
    id: int
    road_name: Optional[str] = None
    length: Optional[float] = None
    geometry_wkt: Optional[str] = None

class LinkResponse(LinkBase):
    model_config = ConfigDict(from_attributes=True)

class LinkDetailResponse(LinkResponse):
    speeds: List[SpeedRecordResponse] = Field(default_factory=list)
    
class AggregateResponse(BaseModel):
    link_id: int
    road_name: Optional[str] = None
    geometry_wkt: Optional[str] = None
    average_speed: float
