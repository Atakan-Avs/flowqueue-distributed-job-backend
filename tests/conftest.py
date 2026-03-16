import os
from uuid import uuid4
from datetime import datetime, UTC

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")


from app.main import app  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.core.rate_limit import rate_limiter  # noqa: E402


class DummyDB:
    def close(self):
        pass


async def override_rate_limiter():
    return None


@pytest.fixture
def client():
    def override_get_db():
        db = DummyDB()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[rate_limiter] = override_rate_limiter

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_job():
    now = datetime.now(UTC)
    return {
        "id": str(uuid4()),
        "job_type": "email",
        "status": "pending",
        "priority": "normal",
        "idempotency_key": None,
        "payload": "send welcome email",
        "result": None,
        "error_message": None,
        "retry_count": 0,
        "is_dead_letter": False,
        "dead_lettered_at": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }