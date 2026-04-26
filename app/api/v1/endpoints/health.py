from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.services.health_service import HealthService

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "flowqueue",
    }


@router.get("/ready")
def readiness_check():
    result = HealthService.check_all()

    if result["status"] == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": "flowqueue",
                "dependencies": result["services"],
            },
        )

    return {
        "status": "ready",
        "service": "flowqueue",
        "dependencies": result["services"],
    }