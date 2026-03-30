from fastapi import APIRouter
from app.api.v1.endpoints import auth, health
from app.api.v1.endpoints import jobs

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(jobs.router, tags=["Jobs"])