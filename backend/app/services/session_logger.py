import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

SESSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sessions"))
SESSION_FILE = os.path.join(SESSIONS_DIR, "audit_session.jsonl")

def ensure_session_storage():
    """Ensures local session directory and log file exist."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    if not os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            pass

def log_session_event(
    event_type: str,
    actor: str = "USER",
    data: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Saves a persistent audit and user action event to local device storage.
    Captures bot chats, approval entries, executions, and database connections.
    """
    ensure_session_storage()
    
    event = {
        "id": f"sess_evt_{uuid.uuid4().hex[:12]}",
        "session_id": session_id or "default_local_session",
        "event_type": event_type,
        "actor": actor,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data or {}
    }

    try:
        with open(SESSION_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        print(f"Failed to write local session event: {e}")

    return event

def get_session_events(limit: int = 200, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves session events from local file storage."""
    ensure_session_storage()
    events = []
    
    if not os.path.exists(SESSION_FILE):
        return []

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        evt = json.loads(line)
                        if session_id and evt.get("session_id") != session_id:
                            continue
                        events.append(evt)
                    except Exception:
                        pass
    except Exception as e:
        print(f"Failed to read local session events: {e}")

    # Return latest events first
    return events[-limit:][::-1]

def clear_session_events():
    """Clears local session logs."""
    ensure_session_storage()
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            pass
    except Exception as e:
        print(f"Failed to clear session storage: {e}")
