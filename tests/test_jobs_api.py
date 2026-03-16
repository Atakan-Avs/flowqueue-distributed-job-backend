from types import SimpleNamespace
from copy import deepcopy
from uuid import uuid4

from app.api.v1.endpoints import jobs as jobs_endpoint


def test_create_job_success(client, monkeypatch, sample_job):
    response_job = SimpleNamespace(**deepcopy(sample_job))

    def fake_create_job(db, job_type, payload, priority, idempotency_key):
        assert job_type == "email"
        assert payload == "send welcome email"
        assert priority == "normal"
        assert idempotency_key is None
        return response_job, True

    captured = {}

    def fake_apply_async(args, queue):
        captured["args"] = args
        captured["queue"] = queue

    monkeypatch.setattr(jobs_endpoint.JobService, "create_job", fake_create_job)
    monkeypatch.setattr(jobs_endpoint.process_job, "apply_async", fake_apply_async)

    response = client.post(
        "/api/v1/jobs",
        json={
            "job_type": "email",
            "payload": "send welcome email",
            "priority": "normal",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["job_type"] == "email"
    assert data["status"] == "pending"
    assert captured["queue"] == "normal"
    assert captured["args"] == [response_job.id]


def test_create_job_duplicate_idempotency_key_returns_existing_job(client, monkeypatch, sample_job):
    job_data = deepcopy(sample_job)
    job_data["idempotency_key"] = "same-key"
    response_job = SimpleNamespace(**job_data)

    def fake_create_job(db, job_type, payload, priority, idempotency_key):
        assert idempotency_key == "same-key"
        return response_job, False

    def fail_apply_async(*args, **kwargs):
        raise AssertionError("Duplicate job should not be queued again")

    monkeypatch.setattr(jobs_endpoint.JobService, "create_job", fake_create_job)
    monkeypatch.setattr(jobs_endpoint.process_job, "apply_async", fail_apply_async)

    response = client.post(
        "/api/v1/jobs",
        json={
            "job_type": "email",
            "payload": "send welcome email",
            "priority": "normal",
        },
        headers={"Idempotency-Key": "same-key"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["idempotency_key"] == "same-key"


def test_create_job_invalid_priority_returns_400(client):
    response = client.post(
        "/api/v1/jobs",
        json={
            "job_type": "email",
            "payload": "send welcome email",
            "priority": "urgent",
        },
    )

    assert response.status_code == 400
    assert "Invalid priority" in response.json()["detail"]


def test_get_job_not_found_returns_404(client, monkeypatch):
    def fake_get_job(db, job_id):
        return None

    monkeypatch.setattr(jobs_endpoint.JobService, "get_job", fake_get_job)

    response = client.get(f"/api/v1/jobs/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_retry_processing_job_returns_400(client, monkeypatch):
    def fake_retry_job(db, job_id):
        return None, "processing"

    monkeypatch.setattr(jobs_endpoint.JobService, "retry_job", fake_retry_job)

    response = client.post(f"/api/v1/jobs/{uuid4()}/retry")

    assert response.status_code == 400
    assert response.json()["detail"] == "Processing jobs cannot be retried"


def test_requeue_non_dead_letter_job_returns_400(client, monkeypatch):
    def fake_requeue_job(db, job_id):
        return None, "not_dead_letter"

    monkeypatch.setattr(jobs_endpoint.JobService, "requeue_dead_letter_job", fake_requeue_job)

    response = client.post(f"/api/v1/jobs/{uuid4()}/requeue")

    assert response.status_code == 400
    assert response.json()["detail"] == "Job is not in dead letter queue"
    
    
def test_retry_completed_job_returns_400(client, monkeypatch):
    def fake_retry_job(db, job_id):
        return None, "completed"

    monkeypatch.setattr(jobs_endpoint.JobService, "retry_job", fake_retry_job)

    response = client.post(f"/api/v1/jobs/{uuid4()}/retry")

    assert response.status_code == 400
    assert response.json()["detail"] == "Completed jobs cannot be retried"


def test_retry_dead_letter_job_returns_400(client, monkeypatch):
    def fake_retry_job(db, job_id):
        return None, "dead_letter"

    monkeypatch.setattr(jobs_endpoint.JobService, "retry_job", fake_retry_job)

    response = client.post(f"/api/v1/jobs/{uuid4()}/retry")

    assert response.status_code == 400
    assert response.json()["detail"] == "Dead letter jobs must be requeued instead of retried"


def test_retry_pending_job_returns_400(client, monkeypatch):
    def fake_retry_job(db, job_id):
        return None, "invalid_status"

    monkeypatch.setattr(jobs_endpoint.JobService, "retry_job", fake_retry_job)

    response = client.post(f"/api/v1/jobs/{uuid4()}/retry")

    assert response.status_code == 400
    assert response.json()["detail"] == "Only failed jobs can be retried"