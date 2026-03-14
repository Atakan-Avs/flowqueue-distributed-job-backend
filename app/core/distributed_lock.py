import uuid

from app.core.redis_client import redis_client


class RedisLock:
    def __init__(self, key: str, timeout: int = 30):
        self.key = key
        self.timeout = timeout
        self.value = str(uuid.uuid4())
        self.acquired = False

    def acquire(self) -> bool:
        self.acquired = bool(
            redis_client.set(
                self.key,
                self.value,
                nx=True,
                ex=self.timeout,
            )
        )
        return self.acquired

    def release(self) -> None:
        current_value = redis_client.get(self.key)
        if current_value == self.value:
            redis_client.delete(self.key)