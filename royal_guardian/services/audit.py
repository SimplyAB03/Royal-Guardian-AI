from sqlalchemy.orm import Session

from royal_guardian.db.models import AuditEvent


def record_audit(db: Session, *, tenant_id: str, actor_type: str, actor_id: str, action: str,
                 target_type: str = "", target_id: str = "", metadata: dict | None = None) -> AuditEvent:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata or {},
    )
    db.add(event)
    db.flush()
    return event
