import uuid

from app.core.redis_client import redis_client


class RedisLock:
    RELEASE_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

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

    def release(self) -> bool:
        result = redis_client.eval(
            self.RELEASE_SCRIPT,
            1,
            self.key,
            self.value,
        )
        return result == 1