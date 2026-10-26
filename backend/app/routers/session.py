from fastapi import APIRouter, Depends, Query, HTTPException, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json

from backend.app.services.session_logger import (
    log_session_event,
    get_session_events,
    clear_session_events,
    SESSION_FILE
)

router = APIRouter(prefix="/api/session", tags=["Session & Local Logging"])

class ClientSessionEvent(BaseModel):
    event_type: str
    actor: str = "USER"
    data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = "local_browser_session"

@router.post("/event")
def record_session_event(event: ClientSessionEvent):
    """
    Records an action performed by user, bot chat, or approved workflow to local system storage.
    """
    saved = log_session_event(
        event_type=event.event_type,
        actor=event.actor,
        data=event.data,
        session_id=event.session_id
    )
    return {"status": "success", "event": saved}

@router.get("/events")
def list_session_events(limit: int = Query(200, ge=1, le=1000), session_id: Optional[str] = None):
    """
    Retrieves all session logs and audit actions stored locally on disk.
    """
    events = get_session_events(limit=limit, session_id=session_id)
    return {
        "status": "success",
        "total_events": len(events),
        "events": events
    }

@router.get("/export")
def export_session_file():
    """
    Exports the complete local session log as JSON.
    """
    events = get_session_events(limit=10000)
    json_bytes = json.dumps(events, indent=2).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=recoveriq_local_session.json"}
    )

@router.delete("/events")
def delete_session_events():
    """
    Clears local session logs on disk.
    """
    clear_session_events()
    return {"status": "success", "message": "Local session logs cleared successfully."}
