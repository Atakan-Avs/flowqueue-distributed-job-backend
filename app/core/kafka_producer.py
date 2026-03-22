import json
import logging

from confluent_kafka import Producer

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_kafka_producer():
    return Producer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
        }
    )


def publish_job_event(event: dict):
    producer = get_kafka_producer()

    try:
        producer.produce(
            settings.kafka_job_events_topic,
            value=json.dumps(event),
        )
        producer.flush()

        logger.info(
            "Kafka event published | event_type=%s | job_id=%s",
            event.get("event_type"),
            event.get("job_id"),
        )

    except Exception as exc:
        logger.error(
            "Kafka publish failed | job_id=%s | error=%s",
            event.get("job_id"),
            str(exc),
        )