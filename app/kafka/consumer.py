import json
import logging
from uuid import UUID, uuid4

from confluent_kafka import Consumer

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import SessionLocal
from app.repositories.job_event_audit_repository import JobEventAuditRepository

setup_logging()
logger = logging.getLogger(__name__)


def run_consumer():
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": "flowqueue-consumer-group-test-2",
            "auto.offset.reset": "earliest",
        }
    )

    consumer.subscribe([settings.kafka_job_events_topic])

    logger.info("Kafka consumer started | topic=%s", settings.kafka_job_events_topic)

    db = SessionLocal()

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                logger.error("Kafka error: %s", msg.error())
                continue

            event = json.loads(msg.value().decode("utf-8"))

            logger.info(
                "Event received | type=%s | job_id=%s | payload=%s",
                event.get("event_type"),
                event.get("job_id"),
                event,
            )

            event_id = UUID(event["event_id"]) if event.get("event_id") else uuid4()

            saved_event = JobEventAuditRepository.create_event_audit(
                db=db,
                event_id=event_id,
                event_type=event["event_type"],
                job_id=UUID(event["job_id"]),
                payload=event,
            )

            if saved_event is None:
                logger.info(
                    "Duplicate event skipped | event_id=%s | job_id=%s",
                    str(event_id),
                    event.get("job_id"),
                )
                continue

            logger.info(
                "Event persisted to audit table | event_id=%s | type=%s | job_id=%s",
                str(event_id),
                event.get("event_type"),
                event.get("job_id"),
            )

    except KeyboardInterrupt:
        logger.info("Kafka consumer stopped by user.")

    finally:
        db.close()
        consumer.close()


if __name__ == "__main__":
    run_consumer()