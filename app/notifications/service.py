import json
from datetime import datetime
from typing import Any

from sqlalchemy import select

from .. import models
from ..models import Notification

ALLOWED_SOURCES = {"openclaw", "human_agent", "watchtower", "system"}
ALLOWED_STATUSES = {"new", "read", "reviewed", "resolved"}
ALLOWED_SEVERITIES = {"info", "success", "warning", "error", "critical"}


def create_notification(
    *,
    source: str,
    recipient: str = "all_human_agents",
    title: str,
    message: str,
    status: str = "new",
    severity: str = "info",
    requires_approval: bool = False,
    approval_status: str | None = None,
    action_id: str | None = None,
    approval_expires_at: datetime | None = None,
    approval_owner_hash: str | None = None,
    task_id: str | None = None,
    task_name: str | None = None,
    report_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    completed_at: datetime | None = None,
    external_url: str | None = None,
) -> Notification:
    source = source.strip().lower()
    recipient = recipient.strip()
    status = status.strip().lower()
    severity = severity.strip().lower()
    if source not in ALLOWED_SOURCES:
        raise ValueError("Invalid notification source")
    if not recipient or len(recipient) > 64:
        raise ValueError("Invalid notification recipient")
    if status not in ALLOWED_STATUSES:
        raise ValueError("Invalid notification status")
    if severity not in ALLOWED_SEVERITIES:
        raise ValueError("Invalid notification severity")
    if not isinstance(requires_approval, bool):
        raise ValueError("requires_approval must be boolean")
    if approval_status is None:
        approval_status = "pending" if requires_approval else "not_required"
    approval_status = approval_status.strip().lower()
    if approval_status not in {"not_required", "pending", "approved", "denied"}:
        raise ValueError("Invalid approval status")
    if requires_approval and approval_status == "not_required":
        approval_status = "pending"
    if not title.strip() or not message.strip():
        raise ValueError("Notification title and message are required")
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":"))

    notification = Notification(
        source=source,
        recipient=recipient,
        title=title.strip(),
        message=message.strip(),
        status=status,
        severity=severity,
        requires_approval=requires_approval,
        approval_status=approval_status,
        action_id=action_id,
        approval_expires_at=approval_expires_at,
        approval_owner_hash=approval_owner_hash,
        task_id=task_id.strip() if task_id else None,
        task_name=task_name.strip() if task_name else None,
        report_id=report_id.strip() if report_id else None,
        metadata_json=metadata_json,
        completed_at=completed_at,
        external_url=external_url.strip() if external_url else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db = models.SessionLocal()
    try:
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def metadata_for(notification: Notification) -> dict[str, Any]:
    try:
        value = json.loads(notification.metadata_json or "{}")
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}
