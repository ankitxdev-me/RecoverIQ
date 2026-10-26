from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.agent.ollama_client import OllamaClient
from backend.app.schemas import SystemHealthResponse

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("", response_model=SystemHealthResponse)
def health_check(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    ollama = OllamaClient()
    ollama_ok, err_msg, details = ollama.check_health()

    status_str = "healthy" if (db_ok and ollama_ok) else "degraded" if db_ok else "unhealthy"

    return SystemHealthResponse(
        status=status_str,
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        simulation_mode=settings.SIMULATION_MODE,
        database_ok=db_ok,
        ollama_ok=ollama_ok,
        ollama_model=settings.OLLAMA_MODEL,
        ollama_details={"error": err_msg} if err_msg else details
    )

@router.get("/ollama")
def ollama_diagnostics():
    ollama = OllamaClient()
    ok, err_msg, details = ollama.check_health()
    return {
        "status": "online" if ok else "offline",
        "endpoint": settings.OLLAMA_BASE_URL,
        "target_model": settings.OLLAMA_MODEL,
        "details": details or {},
        "error": err_msg
    }
