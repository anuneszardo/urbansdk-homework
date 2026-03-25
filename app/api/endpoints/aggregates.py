from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from starlette import status
from app.api.dependencies import get_db
from app.schemas.link import AggregateResponse, LinkDetailResponse, LinkResponse
from app.schemas.spatial import SpatialFilter
from app.schemas.enums import DayOfWeek, TimePeriod
from app.services.analytics import AnalyticsService

router = APIRouter()

@router.get("/", response_model=List[AggregateResponse])
def get_aggregates(
    day: Optional[DayOfWeek] = Query(None, description="Day of the week"),
    period: Optional[TimePeriod] = Query(None, description="Time bucket"),
    limit: int = Query(100, ge=1, le=1000, description="Max links to return"),
    offset: int = Query(0, ge=0, description="Number of links to skip"),
    db: Session = Depends(get_db)
):
    """
    Get average speed per link based on optional day and period. 
    Since it is synchronous and there are large datasets, it is paginated.
    """
    return AnalyticsService.get_aggregate_speeds(db, day=day, period=period, limit=limit, offset=offset)

@router.get("/{link_id}", response_model=LinkDetailResponse)
def get_link_aggregates(
    link_id: int,
    day: Optional[DayOfWeek] = Query(None),
    period: Optional[TimePeriod] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get detailed link info alongside its speed records.
    """
    result = AnalyticsService.get_link_details(db, link_id=link_id, day=day, period=period)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return result

@router.post("/spatial_filter", response_model=List[LinkDetailResponse])
def spatial_filter(
    filter_data: SpatialFilter,
    db: Session = Depends(get_db)
):
    """
    Filter for links within a specific geographic bounding box, including their attached speeds based on optional day/period filters.
    """
    return AnalyticsService.spatial_filter(db, filter_data=filter_data)
