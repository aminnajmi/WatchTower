from datetime import timezone

from .models import Notification, SessionLocal
from .schemas import NotificationCreate


def _database_datetime(value):
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def create_notification(payload: NotificationCreate | dict) -> Notification:
    """Persist every WatchTower, Human Agent, and OpenClaw notification here."""
    if not isinstance(payload, NotificationCreate):
        payload = NotificationCreate.model_validate(payload)
    db = SessionLocal()
    try:
        notification = Notification(
            source=payload.source,
            title=payload.title,
            message=payload.message,
            status=payload.status,
            severity=payload.severity,
            task_id=payload.task_id,
            task_name=payload.task_name,
            report_id=payload.report_id,
            metadata_json=payload.metadata,
            completed_at=_database_datetime(payload.completed_at),
            external_url=payload.external_url,
            requires_review=payload.requires_review,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
