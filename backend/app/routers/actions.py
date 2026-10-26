from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.approval_service import ActionApprovalService
from backend.app.schemas import (
    CaseActionResponse, ActionProposeRequest, ActionExecuteRequest, ActionVerifyRequest
)

router = APIRouter(prefix="/api/actions", tags=["Actions"])

@router.post("/propose", response_model=CaseActionResponse)
def propose_action(req: ActionProposeRequest, db: Session = Depends(get_db)):
    service = ActionApprovalService(db)
    action = service.propose_action(
        case_id=req.case_id,
        action_type=req.action_type,
        payload=req.payload,
        is_simulated=req.is_simulated,
        actor="HUMAN_OPERATOR"
    )
    return action

@router.post("/{action_id}/execute", response_model=CaseActionResponse)
def execute_action(action_id: str, req: ActionExecuteRequest = None, db: Session = Depends(get_db)):
    service = ActionApprovalService(db)
    sim_outcome = req.simulated_outcome if req else None
    action = service.execute_action(action_id=action_id, simulated_outcome=sim_outcome, actor="HUMAN_OPERATOR")
    return action

@router.post("/{action_id}/verify", response_model=CaseActionResponse)
def verify_action(action_id: str, req: ActionVerifyRequest = None, db: Session = Depends(get_db)):
    service = ActionApprovalService(db)
    action, _ = service.verify_action_outcome(action_id=action_id, actor="HUMAN_OPERATOR")
    return action
