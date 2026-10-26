from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import RecoveryCase, ApprovalRecord, AuditEvent
from backend.app.schemas import DashboardSummaryResponse
from backend.app.engine.eligibility import is_eligible_for_recovery
from backend.app.config import settings

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    all_cases = db.query(RecoveryCase).all()

    revenue_at_risk_cents = 0
    eligible_recovery_cents = 0
    confirmed_live_recovered_cents = 0
    simulated_recovered_cents = 0
    open_cases_count = 0

    type_counts = Counter()
    priority_counts = Counter()
    status_counts = Counter()

    for c in all_cases:
        type_counts[c.source_type] += 1
        priority_counts[c.priority] += 1
        status_counts[c.status] += 1

        if not c.is_resolved:
            open_cases_count += 1
            revenue_at_risk_cents += c.amount_cents
            eligible, _ = is_eligible_for_recovery(
                c.source_type, c.status, c.is_resolved, c.retry_count, c.max_retries, c.cooldown_until, c.failure_reason
            )
            if eligible:
                eligible_recovery_cents += c.amount_cents
        else:
            if c.resolution_outcome == "RECOVERED_LIVE":
                confirmed_live_recovered_cents += c.amount_cents
            elif c.resolution_outcome == "RECOVERED_SIMULATED":
                simulated_recovered_cents += c.amount_cents

    pending_approvals = db.query(ApprovalRecord).filter(ApprovalRecord.status == "PENDING").count()

    # Recovery Success Rate:
    # Denominator: All closed cases where recovery was attempted (RECOVERED_LIVE, RECOVERED_SIMULATED, FAILED_PERMANENT, MANUALLY_CLOSED)
    closed_attempted = [c for c in all_cases if c.is_resolved and c.retry_count > 0]
    successful_cases = [c for c in closed_attempted if c.resolution_outcome in ("RECOVERED_LIVE", "RECOVERED_SIMULATED")]
    
    if closed_attempted:
        success_rate = round((len(successful_cases) / len(closed_attempted)) * 100.0, 1)
    else:
        success_rate = 0.0

    denominator_explanation = f"{len(successful_cases)} successful out of {len(closed_attempted)} completed recovery attempts."

    # Recent activity from audit log
    recent_audits = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(8).all()
    recent_activity = [
        {
            "id": a.id,
            "event_type": a.event_type,
            "actor": a.actor,
            "description": a.description,
            "is_simulated": a.is_simulated,
            "case_id": a.case_id,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in recent_audits
    ]

    return DashboardSummaryResponse(
        revenue_at_risk_cents=revenue_at_risk_cents,
        eligible_recovery_cents=eligible_recovery_cents,
        confirmed_live_recovered_cents=confirmed_live_recovered_cents,
        simulated_recovered_cents=simulated_recovered_cents,
        open_cases_count=open_cases_count,
        pending_approvals_count=pending_approvals,
        revenue_at_risk_display=f"${revenue_at_risk_cents / 100:,.2f}",
        eligible_recovery_display=f"${eligible_recovery_cents / 100:,.2f}",
        confirmed_live_recovered_display=f"${confirmed_live_recovered_cents / 100:,.2f}",
        simulated_recovered_display=f"${simulated_recovered_cents / 100:,.2f}",
        recovery_success_rate_percent=success_rate,
        recovery_denominator_explanation=denominator_explanation,
        cases_by_type=dict(type_counts),
        cases_by_priority=dict(priority_counts),
        cases_by_status=dict(status_counts),
        recent_activity=recent_activity,
        simulation_mode=settings.SIMULATION_MODE
    )
