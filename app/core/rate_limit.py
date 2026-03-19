import time

from fastapi import HTTPException, Request

from app.core.redis_client import redis_client

DEFAULT_LIMITS = {
    ("POST", "/api/v1/jobs"): (20, 60),
    ("GET", "/api/v1/jobs"): (120, 60),
    ("GET", "/api/v1/jobs/dead-letter"): (60, 60),
    ("GET", "/api/v1/metrics/jobs"): (60, 60),
    ("POST", "/api/v1/jobs/{job_id}/retry"): (20, 60),
    ("POST", "/api/v1/jobs/{job_id}/requeue"): (20, 60),
}

FALLBACK_LIMIT = (60, 60)


def _normalize_path(path: str) -> str:
    parts = path.strip("/").split("/")

    if len(parts) >= 5 and parts[:3] == ["api", "v1", "jobs"]:
        if len(parts) == 5 and parts[4] in {"retry", "requeue"}:
            return "/api/v1/jobs/{job_id}/" + parts[4]
        if len(parts) == 4 and parts[3] not in {"dead-letter"}:
            return "/api/v1/jobs/{job_id}"

    return path


def _resolve_limit(request: Request) -> tuple[int, int]:
    normalized_path = _normalize_path(request.url.path)
    return DEFAULT_LIMITS.get(
        (request.method.upper(), normalized_path),
        FALLBACK_LIMIT,
    )


async def rate_limiter(request: Request):
    limit, window = _resolve_limit(request)

    api_key = request.headers.get("X-API-Key")
    client_ip = request.client.host if request.client else "unknown"
    identity = api_key.strip() if api_key else client_ip

    now = time.time()
    window_start = now - window

    normalized_path = _normalize_path(request.url.path)
    redis_key = f"rate_limit:{request.method.upper()}:{normalized_path}:{identity}"

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(redis_key, 0, window_start)
    pipe.zcard(redis_key)
    pipe.zadd(redis_key, {str(now): now})
    pipe.expire(redis_key, window)
    _, current_count, _, _ = pipe.execute()

    if current_count >= limit:
        oldest_entries = redis_client.zrange(redis_key, 0, 0, withscores=True)
        retry_after = 1

        if oldest_entries:
            oldest_score = oldest_entries[0][1]
            retry_after = max(1, int(window - (now - oldest_score)))

        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={"Retry-After": str(retry_after)},
        )