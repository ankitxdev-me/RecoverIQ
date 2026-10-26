import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models import AuditEvent

def log_audit(
    db: Session,
    event_type: str,
    actor: str,
    description: str,
    case_id: Optional[str] = None,
    action_id: Optional[str] = None,
    is_simulated: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    event = AuditEvent(
        case_id=case_id,
        action_id=action_id,
        event_type=event_type,
        actor=actor,
        is_simulated=is_simulated,
        description=description,
        metadata_json=json.dumps(metadata or {})
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
