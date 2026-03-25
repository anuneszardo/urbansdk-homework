from typing import Generator
from app.db.session import SessionLocal

def get_db() -> Generator:
    """
    Dependency to get a database session for a single request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
