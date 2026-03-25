import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

from app.main import app
from app.api.dependencies import get_db
from app.core.config import settings
from app.models.base import Base
from app.models.link import Link
from app.models.speed_record import SpeedRecord
from app.schemas.enums import DayOfWeek, TimePeriod

engine = create_engine(settings.TEST_DATABASE_URL)

@pytest.fixture(scope="session")
def db_engine():
    """
    We must create all the models before tests run, 
    and tear them down afterwards.
    """
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    """
    Creates a fresh database session for each test and rolls it back 
    after the test completes.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    """
    Overrides the FastAPI dependency to use the transactional test session.
    """
    def override_get_db():
        yield db
        
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def setup_test_data(db):
    """
    Inserts seed spatial and speed data for tests.
    """
    geometry = from_shape(LineString([(-81.5, 30.0), (-81.5, 30.1)]), srid=4326)
    link1 = Link(
        id=9999991, 
        road_name="Test Road A", 
        length=1.5,
        geometry=geometry
    )
    geometry2 = from_shape(LineString([(-81.2, 30.0), (-81.2, 30.1)]), srid=4326)
    link2 = Link(
        id=9999992, 
        road_name="Test Road B", 
        length=2.5,
        geometry=geometry2
    )
    db.add_all([link1, link2])
    db.flush()

    sr1 = SpeedRecord(
        link_id=9999991,
        timestamp=datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
        speed=25.0,
        day_of_week=DayOfWeek.MONDAY.value,
        time_period=TimePeriod.AM_PEAK.value
    )
    sr2 = SpeedRecord(
        link_id=9999991,
        timestamp=datetime(2024, 1, 1, 8, 30, 0, tzinfo=timezone.utc),
        speed=15.0, 
        day_of_week=DayOfWeek.MONDAY.value,
        time_period=TimePeriod.AM_PEAK.value
    )
    sr3 = SpeedRecord(
        link_id=9999992,
        timestamp=datetime(2024, 1, 1, 17, 0, 0, tzinfo=timezone.utc),
        speed=45.0,
        day_of_week=DayOfWeek.MONDAY.value,
        time_period=TimePeriod.PM_PEAK.value
    )
    db.add_all([sr1, sr2, sr3])
    db.flush()
