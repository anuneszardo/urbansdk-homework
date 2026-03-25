from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api.dependencies import get_db
from app.schemas.enums import TimePeriod
from app.services.analytics import AnalyticsService

router = APIRouter()

@router.get("/slow_links", response_model=List[Dict[str, Any]])
def get_slow_links(
    period: TimePeriod = Query(..., description="Time bucket"),
    threshold: float = Query(..., description="Speed threshold to consider 'slow' (e.g. 15.0)"),
    min_days: int = Query(..., description="Minimum number of slow days required to match"),
    limit: int = Query(100, ge=1, le=1000, description="Max links to return"),
    offset: int = Query(0, ge=0, description="Number of links to skip"),
    db: Session = Depends(get_db)
):
    """
    Find links that are consistently slow over multiple days within a specific time period.
    Since it is synchronous and there are large datasets, it is paginated.
    """
    return AnalyticsService.get_slow_links(db, period=period, threshold=threshold, min_days=min_days, limit=limit, offset=offset)
