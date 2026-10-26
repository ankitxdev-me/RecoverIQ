import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.models import RecoveryCase, RecoveryAction, ApprovalRecord
from backend.app.config import settings
from backend.app.services.audit_service import log_audit
from backend.app.integrations.simulated_provider import (
    SimulatedPaymentProvider, SimulatedCommunicationProvider
)
from backend.app.engine.eligibility import is_eligible_for_recovery

simulated_gateway = SimulatedPaymentProvider()
simulated_comms = SimulatedCommunicationProvider()

class ActionApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def propose_action(
        self,
        case_id: str,
        action_type: str,
        payload: Optional[Dict[str, Any]] = None,
        is_simulated: bool = True,
        actor: str = "AI_AGENT"
    ) -> RecoveryAction:
        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Recovery case {case_id} not found.")

        # Check eligibility
        eligible, reason = is_eligible_for_recovery(
            source_type=case.source_type,
            status=case.status,
            is_resolved=case.is_resolved,
            retry_count=case.retry_count,
            max_retries=case.max_retries,
            cooldown_until=case.cooldown_until,
            failure_reason=case.failure_reason or ""
        )
        if not eligible:
            raise HTTPException(status_code=400, detail=f"Case is not eligible for action: {reason}")

        # Check for existing active/pending action to prevent duplicate execution
        existing_action = self.db.query(RecoveryAction).filter(
            RecoveryAction.case_id == case_id,
            RecoveryAction.status.in_(["PROPOSED", "PENDING_APPROVAL", "APPROVED", "EXECUTING"])
        ).first()
        if existing_action:
            raise HTTPException(
                status_code=409,
                detail=f"An active action ({existing_action.id}, status: {existing_action.status}) is already in progress for this case."
            )

        # Idempotency key
        idem_key = f"idem_{case_id}_{action_type}_{case.retry_count + 1}_{uuid.uuid4().hex[:6]}"

        # Protected action requirements
        requires_approval = False
        potential_consequence = ""

        if case.amount_cents >= settings.REQUIRE_APPROVAL_OVER_AMOUNT_CENTS:
            requires_approval = True
            potential_consequence = f"High monetary value (${case.amount_cents/100:.2f}). Direct oversight required."
        elif "RETRY" in action_type:
            requires_approval = True
            potential_consequence = "Triggering simulated card charge retry on customer account."
        elif "DISCOUNT" in action_type or "INCENTIVE" in action_type:
            requires_approval = True
            potential_consequence = "Issuing recovery promotion or discount."
        elif "DEMAND" in action_type:
            requires_approval = True
            potential_consequence = "Formal overdue debt notification with potential service suspension."
        else:
            requires_approval = False
            potential_consequence = "Standard recovery notice."

        action_status = "PENDING_APPROVAL" if requires_approval else "APPROVED"

        action = RecoveryAction(
            id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
            case_id=case_id,
            action_type=action_type,
            is_simulated=is_simulated,
            idempotency_key=idem_key,
            status=action_status,
            requires_approval=requires_approval,
            proposed_payload=json.dumps(payload or {}),
            execution_result="{}",
            verification_status="UNVERIFIED"
        )
        self.db.add(action)

        if requires_approval:
            approval = ApprovalRecord(
                id=f"APP-{uuid.uuid4().hex[:8].upper()}",
                action_id=action.id,
                case_id=case_id,
                status="PENDING",
                reviewer="PENDING_HUMAN_REVIEW",
                reason=f"Action '{action_type}' proposed for case {case_id} (${case.amount_cents/100:.2f})",
                potential_consequence=potential_consequence
            )
            self.db.add(approval)
            case.status = "PENDING_APPROVAL"
        else:
            case.status = "APPROVED"

        self.db.commit()
        self.db.refresh(action)

        log_audit(
            self.db,
            event_type="APPROVAL_REQUESTED" if requires_approval else "RECOMMENDATION_MADE",
            actor=actor,
            description=f"Action '{action_type}' proposed for case {case_id} ({'Requires human approval' if requires_approval else 'Pre-approved'}).",
            case_id=case_id,
            action_id=action.id,
            is_simulated=is_simulated,
            metadata={"payload": payload, "requires_approval": requires_approval}
        )

        return action

    def review_approval(
        self,
        action_id: str,
        decision: str,
        reviewer: str = "HUMAN_OPERATOR",
        reason: Optional[str] = None
    ) -> RecoveryAction:
        action = self.db.query(RecoveryAction).filter(RecoveryAction.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail=f"Action {action_id} not found.")

        approval = self.db.query(ApprovalRecord).filter(ApprovalRecord.action_id == action_id).first()
        if not approval:
            raise HTTPException(status_code=404, detail=f"No approval record found for action {action_id}.")

        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == action.case_id).first()

        now = datetime.now(timezone.utc)
        if decision == "APPROVE":
            approval.status = "APPROVED"
            approval.reviewer = reviewer
            approval.reason = reason or "Approved by operator."
            approval.reviewed_at = now
            action.status = "APPROVED"
            if case:
                case.status = "APPROVED"

            log_audit(
                self.db,
                event_type="APPROVAL_GRANTED",
                actor=reviewer,
                description=f"Human operator approved action '{action.action_type}' for case {action.case_id}.",
                case_id=action.case_id,
                action_id=action.id,
                is_simulated=action.is_simulated,
                metadata={"reason": reason}
            )
        elif decision == "REJECT":
            approval.status = "REJECTED"
            approval.reviewer = reviewer
            approval.reason = reason or "Rejected by operator."
            approval.reviewed_at = now
            action.status = "REJECTED"
            if case:
                case.status = "ACTION_REQUIRED"

            log_audit(
                self.db,
                event_type="APPROVAL_REJECTED",
                actor=reviewer,
                description=f"Human operator rejected action '{action.action_type}' for case {action.case_id}.",
                case_id=action.case_id,
                action_id=action.id,
                is_simulated=action.is_simulated,
                metadata={"reason": reason}
            )
        else:
            raise HTTPException(status_code=400, detail="Decision must be APPROVE or REJECT.")

        self.db.commit()
        self.db.refresh(action)
        return action

    def execute_action(
        self,
        action_id: str,
        simulated_outcome: Optional[str] = None,
        actor: str = "HUMAN_OPERATOR"
    ) -> RecoveryAction:
        action = self.db.query(RecoveryAction).filter(RecoveryAction.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail=f"Action {action_id} not found.")

        if action.status != "APPROVED":
            raise HTTPException(
                status_code=400,
                detail=f"Action {action_id} cannot be executed because status is '{action.status}' (must be 'APPROVED')."
            )

        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == action.case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Associated case not found.")

        now = datetime.now(timezone.utc)
        action.status = "EXECUTING"
        case.status = "EXECUTING"
        self.db.commit()

        # Execute through controlled simulated provider
        outcome_to_use = simulated_outcome or "SUCCESS"
        result_payload = {}
        error_msg = None

        if "RETRY" in action.action_type:
            res = simulated_gateway.retry_payment(
                transaction_id=case.source_id,
                amount_cents=case.amount_cents,
                currency=case.currency,
                idempotency_key=action.idempotency_key,
                forced_outcome=outcome_to_use
            )
            result_payload = res.model_dump(mode="json")
            if not res.success:
                error_msg = res.error_message
        else:
            # Simulated notification / reminder / link
            cust_email = case.customer.email if case.customer else "customer@example.com"
            res = simulated_comms.send_simulated_reminder(
                recipient=cust_email,
                subject=f"Recovery Notice: {case.id}",
                body=f"Important message regarding {case.source_type} for ${case.amount_cents/100:.2f}."
            )
            result_payload = res.model_dump(mode="json")

        action.execution_result = json.dumps(result_payload)
        action.executed_at = now
        action.status = "EXECUTED"
        case.retry_count += 1
        case.last_attempt_at = now
        # Cooldown of 24h
        case.cooldown_until = now + timedelta(hours=settings.DEFAULT_COOLDOWN_HOURS)
        case.status = "VERIFYING"  # Must be verified before counted as recovered!

        log_audit(
            self.db,
            event_type="ACTION_EXECUTED",
            actor=actor,
            description=f"Executed simulated action '{action.action_type}' for case {case.id}.",
            case_id=case.id,
            action_id=action.id,
            is_simulated=action.is_simulated,
            metadata={"result": result_payload}
        )

        self.db.commit()
        self.db.refresh(action)
        return action

    def verify_action_outcome(
        self,
        action_id: str,
        actor: str = "SYSTEM_ENGINE"
    ) -> Tuple[RecoveryAction, RecoveryCase]:
        """
        Critical Rule: Never mark recovered merely because action was executed.
        Must explicitly verify the simulated gateway or receipt outcome!
        """
        action = self.db.query(RecoveryAction).filter(RecoveryAction.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail=f"Action {action_id} not found.")

        if action.status != "EXECUTED":
            raise HTTPException(
                status_code=400,
                detail=f"Action {action_id} cannot be verified from status '{action.status}' (must be 'EXECUTED')."
            )

        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == action.case_id).first()
        now = datetime.now(timezone.utc)

        result_data = {}
        try:
            result_data = json.loads(action.execution_result or "{}")
        except Exception:
            pass

        # Check if the execution succeeded
        exec_success = result_data.get("success", False)
        status_val = result_data.get("status", "")

        if exec_success and status_val in ("SUCCEEDED", "DELIVERED"):
            # Verified success!
            action.verification_status = "VERIFIED_CONFIRMED"
            action.verified_at = now
            action.status = "VERIFIED_SUCCESS"

            # Check if this action represents an actual revenue recovery (payment retry or paid invoice link)
            # or simply an informational reminder
            if "RETRY" in action.action_type:
                if action.is_simulated:
                    case.status = "RECOVERED_SIMULATED"
                    case.resolution_outcome = "RECOVERED_SIMULATED"
                else:
                    case.status = "RECOVERED_LIVE"
                    case.resolution_outcome = "RECOVERED_LIVE"
                case.is_resolved = True
                case.recovered_at = now
            else:
                # Reminders sent: action verified delivered, but revenue recovery remains pending customer payment
                case.status = "ACTION_REQUIRED"
                case.resolution_outcome = "NONE"

            log_audit(
                self.db,
                event_type="ACTION_VERIFIED",
                actor=actor,
                description=f"Action {action.id} verified: confirmed successful ({action.verification_status}).",
                case_id=case.id,
                action_id=action.id,
                is_simulated=action.is_simulated,
                metadata={"outcome": case.resolution_outcome, "status": case.status}
            )

        else:
            action.verification_status = "VERIFIED_FAILED"
            action.verified_at = now
            action.status = "VERIFIED_FAILURE"
            action.error_message = result_data.get("error_message", "Execution did not achieve recovery clearance.")

            if case.retry_count >= case.max_retries:
                case.status = "FAILED"
                case.resolution_outcome = "FAILED_PERMANENT"
                case.is_resolved = True
            else:
                case.status = "ACTION_REQUIRED"

            log_audit(
                self.db,
                event_type="ACTION_FAILED",
                actor=actor,
                description=f"Action {action.id} verified failed: {action.error_message}",
                case_id=case.id,
                action_id=action.id,
                is_simulated=action.is_simulated,
                metadata={"error": action.error_message}
            )

        self.db.commit()
        self.db.refresh(action)
        self.db.refresh(case)
        return action, case
