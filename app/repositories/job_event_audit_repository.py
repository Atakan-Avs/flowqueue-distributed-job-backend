import json
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.job_event_audit import JobEventAudit


class JobEventAuditRepository:
    @staticmethod
    def create_event_audit(
        db: Session,
        event_type: str,
        job_id: uuid.UUID,
        payload: dict,
    ) -> JobEventAudit:
        event_audit = JobEventAudit(
            event_type=event_type,
            job_id=job_id,
            payload=json.dumps(payload),
            consumed_at=datetime.utcnow(),
        )
        db.add(event_audit)
        db.commit()
        db.refresh(event_audit)
        return event_audit