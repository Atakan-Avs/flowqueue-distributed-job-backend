from fastapi import Depends, HTTPException, Request
from app.core.redis_client import redis_client
from app.db.models.user import User
from app.core.dependencies import get_current_user


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds

    def __call__(self, request: Request, user: User = Depends(get_current_user)):
        key = f"rate_limit:{request.url.path}:{user.id}"

        current_count = redis_client.incr(key)

        if current_count == 1:
            redis_client.expire(key, self.window)

        if current_count > self.limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            )