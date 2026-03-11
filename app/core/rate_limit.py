import time

from fastapi import Request, HTTPException

from app.core.redis_client import redis_client


RATE_LIMIT = 60  # requests
WINDOW = 60      # seconds


async def rate_limiter(request: Request):

    client_ip = request.client.host

    key = f"rate_limit:{client_ip}"

    current = redis_client.get(key)

    if current is None:
        redis_client.set(key, 1, ex=WINDOW)
        return

    current = int(current)

    if current >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
        )

    redis_client.incr(key)