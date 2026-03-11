from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def startup_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@app.get("/")
def root():
    return {
        "message": "FlowQueue API is running"
    }