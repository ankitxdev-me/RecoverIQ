from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.database import get_db
from backend.app.models import RecoveryCase, Customer
from backend.app.schemas import RecoveryCaseResponse

router = APIRouter(prefix="/api/cases", tags=["Recovery Cases"])

@router.get("", response_model=List[RecoveryCaseResponse])
def list_cases(
    search: Optional[str] = Query(None, description="Search by case ID, source ID, customer name/email"),
    source_type: Optional[str] = Query(None, description="failed_payment, overdue_invoice, abandoned_checkout"),
    status: Optional[str] = Query(None, description="Case status filter"),
    priority: Optional[str] = Query(None, description="CRITICAL, HIGH, MEDIUM, LOW"),
    is_resolved: Optional[bool] = Query(None, description="Filter resolved/unresolved"),
    sort_by: str = Query("priority_score", description="priority_score, amount, created_at"),
    db: Session = Depends(get_db)
):
    query = db.query(RecoveryCase).join(Customer)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                RecoveryCase.id.ilike(s),
                RecoveryCase.source_id.ilike(s),
                RecoveryCase.failure_reason.ilike(s),
                Customer.name.ilike(s),
                Customer.email.ilike(s),
                Customer.customer_ref.ilike(s)
            )
        )

    if source_type:
        query = query.filter(RecoveryCase.source_type == source_type)

    if status:
        query = query.filter(RecoveryCase.status == status)

    if priority:
        query = query.filter(RecoveryCase.priority == priority)

    if is_resolved is not None:
        query = query.filter(RecoveryCase.is_resolved == is_resolved)

    if sort_by == "amount":
        query = query.order_by(RecoveryCase.amount_cents.desc())
    elif sort_by == "created_at":
        query = query.order_by(RecoveryCase.created_at.desc())
    else:
        query = query.order_by(RecoveryCase.priority_score.desc())

    return query.all()

@router.get("/{case_id}", response_model=RecoveryCaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case
