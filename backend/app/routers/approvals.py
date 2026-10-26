from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import ApprovalRecord
from backend.app.schemas import ApprovalResponse, ApprovalDecisionRequest, CaseActionResponse
from backend.app.services.approval_service import ActionApprovalService

from backend.app.services.session_logger import log_session_event

router = APIRouter(tags=["Approvals"])

@router.get("/api/approvals", response_model=List[ApprovalResponse])
def list_approvals(db: Session = Depends(get_db)):
    approvals = db.query(ApprovalRecord).order_by(ApprovalRecord.created_at.desc()).all()
    return approvals

@router.post("/api/actions/{action_id}/approve", response_model=CaseActionResponse)
def approve_action(action_id: str, req: ApprovalDecisionRequest = None, db: Session = Depends(get_db)):
    service = ActionApprovalService(db)
    reason = req.reason if req else "Approved by human operator"
    reviewer = req.reviewer if req else "HUMAN_OPERATOR"
    action = service.review_approval(action_id=action_id, decision="APPROVE", reviewer=reviewer, reason=reason)
    
    # Store approved action event to local device session
    log_session_event(
        event_type="ACTION_APPROVED",
        actor=reviewer,
        data={
            "action_id": action_id,
            "case_id": action.case_id,
            "action_type": action.action_type,
            "decision": "APPROVE",
            "reason": reason,
            "reviewer": reviewer
        }
    )
    return action

@router.post("/api/actions/{action_id}/reject", response_model=CaseActionResponse)
def reject_action(action_id: str, req: ApprovalDecisionRequest = None, db: Session = Depends(get_db)):
    service = ActionApprovalService(db)
    reason = req.reason if req else "Rejected by human operator"
    reviewer = req.reviewer if req else "HUMAN_OPERATOR"
    action = service.review_approval(action_id=action_id, decision="REJECT", reviewer=reviewer, reason=reason)
    
    # Store rejected action event to local device session
    log_session_event(
        event_type="ACTION_REJECTED",
        actor=reviewer,
        data={
            "action_id": action_id,
            "case_id": action.case_id,
            "action_type": action.action_type,
            "decision": "REJECT",
            "reason": reason,
            "reviewer": reviewer
        }
    )
    return action
