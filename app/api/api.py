from fastapi import APIRouter
from app.api.endpoints import aggregates, patterns

api_router = APIRouter()

api_router.include_router(aggregates.router, prefix="/aggregates", tags=["Aggregates"])
api_router.include_router(patterns.router, prefix="/patterns", tags=["Patterns"])
