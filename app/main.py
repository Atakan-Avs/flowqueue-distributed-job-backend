import logging

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.request_id import RequestIDMiddleware
from app.db.session import engine

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(RequestIDMiddleware)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def startup_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    logger.info("Application startup completed successfully")


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "FlowQueue API is running"
    }


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )