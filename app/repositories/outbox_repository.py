import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.outbox_event import OutboxEvent


class OutboxRepository:
    @staticmethod
    def create_event(
        db: Session,
        event_type: str,
        aggregate_id: uuid.UUID,
        payload: dict,
    ) -> OutboxEvent:
        event = OutboxEvent(
            event_type=event_type,
            aggregate_id=aggregate_id,
            payload=json.dumps(payload),
            created_at=datetime.utcnow(),
            published_at=None,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_unpublished_events(db: Session, limit: int = 100) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def mark_as_published(db: Session, event: OutboxEvent) -> OutboxEvent:
        event.published_at = datetime.utcnow()
        db.add(event)
        db.commit()
        db.refresh(event)
        return event