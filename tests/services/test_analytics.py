from app.services.analytics import AnalyticsService
from app.schemas.spatial import SpatialFilter
from app.schemas.enums import DayOfWeek, TimePeriod

class TestAnalyticsService:
    def test_get_aggregate_speeds(self, db, setup_test_data):
        results = AnalyticsService.get_aggregate_speeds(
            db, day=DayOfWeek.MONDAY, period=TimePeriod.AM_PEAK, limit=10
        )
        assert len(results) == 1
        assert results[0]["link_id"] == 9999991
        assert results[0]["average_speed"] == 20.0
    
    def test_get_aggregate_speeds_empty_data(self, db):
        results = AnalyticsService.get_aggregate_speeds(
            db, day=DayOfWeek.SUNDAY, period=TimePeriod.EVENING
        )
        assert results == []

    def test_get_aggregate_speeds_with_pagination(self, db, setup_test_data):
        results = AnalyticsService.get_aggregate_speeds(
            db, day=DayOfWeek.MONDAY, period=TimePeriod.AM_PEAK, limit=1
        )
        assert len(results) == 1
        assert results[0]["link_id"] == 9999991
        assert results[0]["average_speed"] == 20.0

    def test_get_link_details(self, db, setup_test_data):
        result = AnalyticsService.get_link_details(
            db, link_id=9999991, day=DayOfWeek.MONDAY, period=TimePeriod.AM_PEAK
        )
        assert result is not None
        assert result["id"] == 9999991
        assert len(result["speeds"]) == 2

    def test_get_slow_links(self, db, setup_test_data):
        results = AnalyticsService.get_slow_links(
            db, period=TimePeriod.AM_PEAK, threshold=22.0, min_days=1, limit=10
        )
        assert len(results) == 1
        assert results[0]["link_id"] == 9999991

    def test_spatial_filter(self, db, setup_test_data):
        filter_data = SpatialFilter(
            min_lon=-81.6, min_lat=29.5, max_lon=-81.4, max_lat=30.5,
            day=DayOfWeek.MONDAY, period=TimePeriod.AM_PEAK
        )
        results = AnalyticsService.spatial_filter(db, filter_data=filter_data)
        assert len(results) == 1
        assert results[0]["id"] == 9999991
    
    def test_spatial_filter_no_results(self, db, setup_test_data):
        filter_data = SpatialFilter(
            min_lon=0, min_lat=0, max_lon=1, max_lat=1,
            day=DayOfWeek.MONDAY, period=TimePeriod.AM_PEAK
        )
        results = AnalyticsService.spatial_filter(db, filter_data=filter_data)
        assert results == []
