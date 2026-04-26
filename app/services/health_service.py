from sqlalchemy import text

from app.core.kafka_producer import get_kafka_producer
from app.core.redis_client import redis_client
from app.db.session import SessionLocal


class HealthService:
    @staticmethod
    def check_database() -> bool:
        db = None

        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            if db:
                db.close()

    @staticmethod
    def check_redis() -> bool:
        try:
            return redis_client.ping() is True
        except Exception:
            return False

    @staticmethod
    def check_kafka() -> bool:
        producer = None

        try:
            producer = get_kafka_producer()
            metadata = producer.list_topics(timeout=3)
            return metadata is not None
        except Exception:
            return False
        finally:
            if producer:
                producer.flush(1)

    @classmethod
    def check_all(cls) -> dict:
        database_ok = cls.check_database()
        redis_ok = cls.check_redis()
        kafka_ok = cls.check_kafka()

        is_healthy = database_ok and redis_ok and kafka_ok

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "services": {
                "database": "ok" if database_ok else "failed",
                "redis": "ok" if redis_ok else "failed",
                "kafka": "ok" if kafka_ok else "failed",
            },
        }