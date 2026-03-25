from fastapi import FastAPI
from app.api.api import api_router
from app.core.config import settings
from app.db.session import engine
from app.models.base import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Geospatial Traffic Data Microservice",
    version="1.0.0",
)

app.include_router(api_router)

@app.get("/healthz", tags=["Health"])
def health_check():
    return {"status": "ok"}
