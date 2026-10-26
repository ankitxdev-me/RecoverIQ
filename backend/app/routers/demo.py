from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.seed import reset_and_seed_database
from backend.app.services.audit_service import log_audit

router = APIRouter(prefix="/api/demo", tags=["Demo Management"])

@router.post("/reset")
def reset_demo(db: Session = Depends(get_db)):
    reset_and_seed_database(db)
    log_audit(
        db,
        event_type="DEMO_RESET",
        actor="HUMAN_OPERATOR",
        description="Demo database was restored to baseline seed state with deterministic multi-case records.",
        is_simulated=True
    )
    return {
        "status": "success",
        "message": "Demo data has been successfully reset to initial deterministic state."
    }
