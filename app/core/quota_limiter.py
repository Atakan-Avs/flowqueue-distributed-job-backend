from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request

from app.core.dependencies import get_current_user
from app.core.redis_client import redis_client
from app.db.models.user import User


class DailyQuotaLimiter:
    def __init__(self, limit: int):
        self.limit = limit

    def __call__(
        self,
        request: Request,
        user: User = Depends(get_current_user),
    ):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"quota:{request.url.path}:{today}:{user.id}"

        current_count = redis_client.incr(key)

        if current_count == 1:
            redis_client.expire(key, self._seconds_until_midnight_utc())

        if current_count > self.limit:
            raise HTTPException(
                status_code=429,
                detail="Daily job quota exceeded. Please try again tomorrow.",
            )

    @staticmethod
    def _seconds_until_midnight_utc() -> int:
        now = datetime.now(timezone.utc)
        tomorrow = now.date() + timedelta(days=1)
        midnight = datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc)
        return int((midnight - now).total_seconds())