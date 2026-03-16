from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.services.job_service import JobService


def test_retry_job_updates_state(monkeypatch):
    job = SimpleNamespace(
        id=uuid4(),
        status="failed",
        result="old result",
        error_message="old error",
        retry_count=1,
    )

    def fake_get_by_id(db, job_id):
        return job

    def fake_update(db, updated_job):
        return updated_job

    monkeypatch.setattr("app.services.job_service.JobRepository.get_by_id", fake_get_by_id)
    monkeypatch.setattr("app.services.job_service.JobRepository.update", fake_update)

    updated_job, error = JobService.retry_job(db=None, job_id=job.id)

    assert error is None
    assert updated_job.status == "pending"
    assert updated_job.result is None
    assert updated_job.error_message is None
    assert updated_job.retry_count == 2


def test_retry_job_returns_not_found(monkeypatch):
    def fake_get_by_id(db, job_id):
        return None

    monkeypatch.setattr("app.services.job_service.JobRepository.get_by_id", fake_get_by_id)

    updated_job, error = JobService.retry_job(db=None, job_id=uuid4())

    assert updated_job is None
    assert error == "not_found"


def test_retry_job_rejects_processing(monkeypatch):
    job = SimpleNamespace(
        id=uuid4(),
        status="processing",
        result=None,
        error_message=None,
        retry_count=0,
    )

    def fake_get_by_id(db, job_id):
        return job

    monkeypatch.setattr("app.services.job_service.JobRepository.get_by_id", fake_get_by_id)

    updated_job, error = JobService.retry_job(db=None, job_id=job.id)

    assert updated_job is None
    assert error == "processing"


def test_requeue_dead_letter_job_updates_state(monkeypatch):
    job = SimpleNamespace(
        id=uuid4(),
        status="failed",
        result="bad",
        error_message="boom",
        retry_count=3,
        is_dead_letter=True,
        dead_lettered_at="2026-03-16T10:00:00",
    )

    def fake_get_by_id(db, job_id):
        return job

    def fake_update(db, updated_job):
        return updated_job

    monkeypatch.setattr("app.services.job_service.JobRepository.get_by_id", fake_get_by_id)
    monkeypatch.setattr("app.services.job_service.JobRepository.update", fake_update)

    updated_job, error = JobService.requeue_dead_letter_job(db=None, job_id=job.id)

    assert error is None
    assert updated_job.status == "pending"
    assert updated_job.result is None
    assert updated_job.error_message is None
    assert updated_job.is_dead_letter is False
    assert updated_job.dead_lettered_at is None


def test_create_job_returns_existing_job_after_integrity_error(monkeypatch):
    existing_job = SimpleNamespace(
        id=uuid4(),
        job_type="email",
        payload="send welcome email",
        status="pending",
        priority="normal",
        idempotency_key="same-key",
    )

    class DummyDB:
        def __init__(self):
            self.rollback_called = False

        def rollback(self):
            self.rollback_called = True

    db = DummyDB()
    state = {"lookup_count": 0}

    def fake_get_by_idempotency_key(db, idempotency_key):
        state["lookup_count"] += 1
        if state["lookup_count"] == 1:
            return None
        return existing_job

    def fake_create(db, job):
        raise IntegrityError("duplicate key", params=None, orig=Exception("unique violation"))

    monkeypatch.setattr(
        "app.services.job_service.JobRepository.get_by_idempotency_key",
        fake_get_by_idempotency_key,
    )
    monkeypatch.setattr(
        "app.services.job_service.JobRepository.create",
        fake_create,
    )

    job, created = JobService.create_job(
        db=db,
        job_type="email",
        payload="send welcome email",
        priority="normal",
        idempotency_key="same-key",
    )

    assert db.rollback_called is True
    assert created is False
    assert job.idempotency_key == "same-key"


def test_create_job_reraises_integrity_error_without_idempotency_key(monkeypatch):
    class DummyDB:
        def __init__(self):
            self.rollback_called = False

        def rollback(self):
            self.rollback_called = True

    db = DummyDB()

    def fake_create(db, job):
        raise IntegrityError("insert failed", params=None, orig=Exception("db error"))

    monkeypatch.setattr(
        "app.services.job_service.JobRepository.create",
        fake_create,
    )

    with pytest.raises(IntegrityError):
        JobService.create_job(
            db=db,
            job_type="email",
            payload="send welcome email",
            priority="normal",
            idempotency_key=None,
        )

    assert db.rollback_called is True

def test_retry_job_rejects_completed(monkeypatch):
    job = SimpleNamespace(
        id=uuid4(),
        status="completed",
        result="done",
        error_message=None,
        retry_count=0,
        is_dead_letter=False,
    )

    def fake_get_by_id(db, job_id):
        return job

    monkeypatch.setattr("app.services.job_service.JobRepository.get_by_id", fake_get_by_id)

    updated_job, error = JobService.retry_job(db=None, job_id=job.id)

    assert updated_job is None
    assert error == "completed"


def test_retry_job_rejects_dead_letter(monkeypatch):
    job = SimpleNamespace(
        id=uuid4(),
        status="failed",
        result=None,
        error_message="boom",
        retry_count=3,
        is_dead_letter=True,
        dead_lettered_at="2026-03-16T10:00:00",
    )

    def fake_get_by_id(db, job_id):
        return job

    monkeypatch.setattr("app.services.job_service.JobRepository.get_by_id", fake_get_by_id)

    updated_job, error = JobService.retry_job(db=None, job_id=job.id)

    assert updated_job is None
    assert error == "dead_letter"


def test_retry_job_rejects_pending(monkeypatch):
    job = SimpleNamespace(
        id=uuid4(),
        status="pending",
        result=None,
        error_message=None,
        retry_count=0,
        is_dead_letter=False,
    )

    def fake_get_by_id(db, job_id):
        return job

    monkeypatch.setattr("app.services.job_service.JobRepository.get_by_id", fake_get_by_id)

    updated_job, error = JobService.retry_job(db=None, job_id=job.id)

    assert updated_job is None
    assert error == "invalid_status"