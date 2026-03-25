from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from geoalchemy2.functions import ST_MakeEnvelope, ST_Intersects, ST_AsText

from app.models.link import Link
from app.models.speed_record import SpeedRecord
from app.schemas.link import SpeedRecordResponse
from app.schemas.spatial import SpatialFilter
from app.schemas.enums import DayOfWeek, TimePeriod

class AnalyticsService:

    @staticmethod
    def get_aggregate_speeds(
        db: Session, 
        day: Optional[DayOfWeek] = None, 
        period: Optional[TimePeriod] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """
        Calculate average speed per link based on day and period filters.
        """
        query = db.query(
            SpeedRecord.link_id,
            Link.road_name,
            Link.length,
            ST_AsText(Link.geometry).label('geometry_wkt'),
            func.avg(SpeedRecord.speed).label('average_speed')
        ).join(Link, Link.id == SpeedRecord.link_id)
        
        if day is not None:
            query = query.filter(SpeedRecord.day_of_week == day.value)
        if period is not None:
            query = query.filter(SpeedRecord.time_period == period.value)
        
        # GROUP BY must include every non-aggregated projected column
        results = (
            query
            .group_by(SpeedRecord.link_id, Link.road_name, Link.length, Link.geometry)
            .order_by(SpeedRecord.link_id)
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [
            {
                "link_id": r.link_id,
                "road_name": r.road_name,
                "length": r.length,
                "geometry_wkt": r.geometry_wkt,
                "average_speed": float(r.average_speed)
            }
            for r in results
        ]

    @staticmethod
    def get_link_details(db: Session, link_id: int, day: Optional[DayOfWeek] = None, period: Optional[TimePeriod] = None):
        """
        Get detailed link information along with speeds.
        """
        result = db.query(Link, ST_AsText(Link.geometry).label('geometry_wkt')).filter(Link.id == link_id).first()
        if not result:
            return None
        link, geometry_wkt = result
            
        speed_query = db.query(SpeedRecord).filter(SpeedRecord.link_id == link_id)
        if day is not None:
            speed_query = speed_query.filter(SpeedRecord.day_of_week == day.value)
        if period is not None:
            speed_query = speed_query.filter(SpeedRecord.time_period == period.value)
            
        speeds = speed_query.all()
        
        # Format response into dict representation for the schema validation
        result = {
            "id": link.id,
            "road_name": link.road_name,
            "length": link.length,
            "geometry_wkt": geometry_wkt,
            "speeds": [SpeedRecordResponse.model_validate(s) for s in speeds]
        }
        return result

    @staticmethod
    def get_slow_links(
        db: Session, 
        period: TimePeriod, 
        threshold: float, 
        min_days: int,
        limit: int = 100,
        offset: int = 0
    ):
        """
        Identify links that are consistently slow over multiple days.
        """
        # Subquery: avg speed per day per link for the period
        daily_avg_subquery = db.query(
            SpeedRecord.link_id,
            SpeedRecord.day_of_week,
            func.avg(SpeedRecord.speed).label('daily_avg')
        ).filter(
            SpeedRecord.time_period == period.value
        ).group_by(
            SpeedRecord.link_id, SpeedRecord.day_of_week
        ).subquery()
        
        slow_days_count = func.count(daily_avg_subquery.c.day_of_week).label('slow_days')
        avg_speed = func.avg(daily_avg_subquery.c.daily_avg).label('average_speed')
        
        query = db.query(
            daily_avg_subquery.c.link_id,
            slow_days_count,
            avg_speed
        ).filter(
            daily_avg_subquery.c.daily_avg <= threshold
        ).group_by(
            daily_avg_subquery.c.link_id
        ).having(
            func.count(daily_avg_subquery.c.day_of_week) >= min_days
        ).order_by(daily_avg_subquery.c.link_id)
        
        results = query.limit(limit).offset(offset).all()
        return [
            {
                "link_id": r.link_id, 
                "slow_days": r.slow_days, 
                "average_speed": float(r.average_speed) if r.average_speed else 0.0
            } for r in results
        ]

    @staticmethod
    def spatial_filter(db: Session, filter_data: SpatialFilter):
        """
        Filter links within a bounding box using PostGIS and optionally retrieve speed records.
        """
        # Format: ST_MakeEnvelope(xmin, ymin, xmax, ymax, srid)
        envelope = ST_MakeEnvelope(
            filter_data.min_lon, filter_data.min_lat,
            filter_data.max_lon, filter_data.max_lat,
            4326
        )
        
        # We need the geometry as WKT so Pydantic can serialize it.
        results = db.query(Link, ST_AsText(Link.geometry).label('geometry_wkt')).filter(
            ST_Intersects(Link.geometry, envelope)
        ).all()
        
        link_ids = [r.Link.id for r in results]
        
        if not link_ids:
            return []
            
        # Get all relevant speeds sorted by timestamp in one bulk query to prevent N+1 database hits
        speed_query = db.query(SpeedRecord).filter(SpeedRecord.link_id.in_(link_ids))
        if filter_data.day is not None:
            speed_query = speed_query.filter(SpeedRecord.day_of_week == filter_data.day.value)
        if filter_data.period is not None:
            speed_query = speed_query.filter(SpeedRecord.time_period == filter_data.period.value)
        all_speeds = speed_query.order_by(SpeedRecord.timestamp).all()
        
        # Group speeds by link_id into a mapping
        speeds_by_link = {link_id: [] for link_id in link_ids}
        for speed in all_speeds:
            speeds_by_link[speed.link_id].append(speed)
        
        formatted_results = []
        for r in results:
            formatted_results.append({
                "id": r.Link.id,
                "road_name": r.Link.road_name,
                "length": r.Link.length,
                "geometry_wkt": r.geometry_wkt,
                "speeds": speeds_by_link.get(r.Link.id, [])
            })
            
        return formatted_results
