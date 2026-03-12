from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.core.redis_client import redis_client
from app.db.session import engine

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "flowqueue",
    }


@router.get("/ready")
def readiness_check():
    database_status = "ok"
    redis_status = "ok"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    try:
        redis_client.ping()
    except Exception:
        redis_status = "error"

    if database_status == "error" or redis_status == "error":
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "service": "flowqueue",
                "dependencies": {
                    "database": database_status,
                    "redis": redis_status,
                },
            },
        )

    return {
        "status": "ready",
        "service": "flowqueue",
        "dependencies": {
            "database": database_status,
            "redis": redis_status,
        },
    }