from app.core.distributed_lock import RedisLock


class FakeRedis:
    def __init__(self):
        self.store = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    def eval(self, script, numkeys, key, value):
        current_value = self.store.get(key)
        if current_value == value:
            del self.store[key]
            return 1
        return 0


def test_acquire_sets_lock_value(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr("app.core.distributed_lock.redis_client", fake_redis)

    lock = RedisLock("lock:job:123", timeout=30)

    acquired = lock.acquire()

    assert acquired is True
    assert fake_redis.store["lock:job:123"] == lock.value


def test_release_deletes_key_when_value_matches(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr("app.core.distributed_lock.redis_client", fake_redis)

    lock = RedisLock("lock:job:123", timeout=30)
    lock.acquire()

    released = lock.release()

    assert released is True
    assert "lock:job:123" not in fake_redis.store


def test_release_does_not_delete_key_when_value_differs(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr("app.core.distributed_lock.redis_client", fake_redis)

    lock = RedisLock("lock:job:123", timeout=30)
    fake_redis.store["lock:job:123"] = "another-owner"
    lock.value = "my-token"

    released = lock.release()

    assert released is False
    assert fake_redis.store["lock:job:123"] == "another-owner"