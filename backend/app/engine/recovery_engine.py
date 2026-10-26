import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models import (
    Customer, Transaction, Invoice, Checkout, RecoveryCase, RecoveryAction, ApprovalRecord, AuditEvent
)
from backend.app.engine.priority import calculate_priority_score
from backend.app.engine.eligibility import is_eligible_for_recovery, determine_recommended_action

class RecoveryEngine:
    def __init__(self, db: Session):
        self.db = db

    def sync_and_detect_cases(self) -> int:
        """
        Scans all source records (Transactions, Invoices, Checkouts)
        and detects eligible recovery cases that don't already exist.
        Returns count of newly detected cases.
        """
        new_cases_count = 0

        # 1. Detect Failed Payments
        failed_txs = self.db.query(Transaction).filter(
            Transaction.status == "FAILED"
        ).all()
        for tx in failed_txs:
            case_id = f"CASE-PAY-{tx.id}"
            existing = self.db.query(RecoveryCase).filter(
                RecoveryCase.source_type == "failed_payment",
                RecoveryCase.source_id == tx.external_id
            ).first()

            if not existing:
                now = datetime.now(timezone.utc)
                tx_date = tx.created_at
                if tx_date.tzinfo is None:
                    tx_date = tx_date.replace(tzinfo=timezone.utc)
                age_days = max(0, (now - tx_date).days)

                label, score, reasons = calculate_priority_score(
                    amount_cents=tx.amount_cents,
                    source_type="failed_payment",
                    age_days=age_days,
                    retry_count=0,
                    failure_reason=tx.failure_code or tx.failure_reason or ""
                )

                rec_action, _, _ = determine_recommended_action(
                    source_type="failed_payment",
                    failure_reason=tx.failure_code or tx.failure_reason or "",
                    retry_count=0,
                    amount_cents=tx.amount_cents
                )

                new_case = RecoveryCase(
                    id=case_id,
                    source_type="failed_payment",
                    source_id=tx.external_id,
                    customer_id=tx.customer_id,
                    amount_cents=tx.amount_cents,
                    currency=tx.currency,
                    status="DETECTED",
                    priority=label,
                    priority_score=score,
                    priority_reasons=json.dumps(reasons),
                    failure_reason=tx.failure_code or tx.failure_reason or "Payment failed at gateway",
                    recommended_action=rec_action,
                    retry_count=0,
                    max_retries=3,
                    is_resolved=False,
                    resolution_outcome="NONE"
                )
                self.db.add(new_case)
                
                # Audit
                audit = AuditEvent(
                    case_id=case_id,
                    event_type="DETECTED",
                    actor="SYSTEM_ENGINE",
                    is_simulated=True,
                    description=f"Detected failed payment of ${tx.amount_cents/100:.2f} ({tx.failure_code or 'Unknown'})",
                    metadata_json=json.dumps({"external_id": tx.external_id, "priority": label, "score": score})
                )
                self.db.add(audit)
                new_cases_count += 1

        # 2. Detect Overdue Invoices
        overdue_invs = self.db.query(Invoice).filter(
            Invoice.status == "OVERDUE"
        ).all()
        for inv in overdue_invs:
            case_id = f"CASE-INV-{inv.id}"
            existing = self.db.query(RecoveryCase).filter(
                RecoveryCase.source_type == "overdue_invoice",
                RecoveryCase.source_id == inv.invoice_number
            ).first()

            if not existing:
                age_days = inv.days_overdue
                label, score, reasons = calculate_priority_score(
                    amount_cents=inv.amount_cents,
                    source_type="overdue_invoice",
                    age_days=age_days,
                    retry_count=0,
                    failure_reason=f"overdue_{age_days}_days"
                )

                rec_action, _, _ = determine_recommended_action(
                    source_type="overdue_invoice",
                    failure_reason=f"overdue_{age_days}_days",
                    retry_count=0,
                    amount_cents=inv.amount_cents
                )

                new_case = RecoveryCase(
                    id=case_id,
                    source_type="overdue_invoice",
                    source_id=inv.invoice_number,
                    customer_id=inv.customer_id,
                    amount_cents=inv.amount_cents,
                    currency=inv.currency,
                    status="DETECTED",
                    priority=label,
                    priority_score=score,
                    priority_reasons=json.dumps(reasons),
                    failure_reason=f"Invoice overdue by {age_days} days",
                    recommended_action=rec_action,
                    retry_count=0,
                    max_retries=3,
                    is_resolved=False,
                    resolution_outcome="NONE"
                )
                self.db.add(new_case)

                audit = AuditEvent(
                    case_id=case_id,
                    event_type="DETECTED",
                    actor="SYSTEM_ENGINE",
                    is_simulated=True,
                    description=f"Detected overdue invoice {inv.invoice_number} of ${inv.amount_cents/100:.2f} ({age_days} days overdue)",
                    metadata_json=json.dumps({"invoice_number": inv.invoice_number, "priority": label, "score": score})
                )
                self.db.add(audit)
                new_cases_count += 1

        # 3. Detect Abandoned Checkouts
        abandoned_chk = self.db.query(Checkout).filter(
            Checkout.status == "ABANDONED"
        ).all()
        for chk in abandoned_chk:
            case_id = f"CASE-CHK-{chk.id}"
            existing = self.db.query(RecoveryCase).filter(
                RecoveryCase.source_type == "abandoned_checkout",
                RecoveryCase.source_id == chk.checkout_token
            ).first()

            if not existing:
                now = datetime.now(timezone.utc)
                chk_date = chk.abandoned_at
                if chk_date.tzinfo is None:
                    chk_date = chk_date.replace(tzinfo=timezone.utc)
                age_days = max(0, (now - chk_date).days)

                label, score, reasons = calculate_priority_score(
                    amount_cents=chk.amount_cents,
                    source_type="abandoned_checkout",
                    age_days=age_days,
                    retry_count=0,
                    failure_reason="cart_abandoned"
                )

                rec_action, _, _ = determine_recommended_action(
                    source_type="abandoned_checkout",
                    failure_reason="cart_abandoned",
                    retry_count=0,
                    amount_cents=chk.amount_cents
                )

                new_case = RecoveryCase(
                    id=case_id,
                    source_type="abandoned_checkout",
                    source_id=chk.checkout_token,
                    customer_id=chk.customer_id,
                    amount_cents=chk.amount_cents,
                    currency=chk.currency,
                    status="DETECTED",
                    priority=label,
                    priority_score=score,
                    priority_reasons=json.dumps(reasons),
                    failure_reason="Customer dropped off at checkout flow",
                    recommended_action=rec_action,
                    retry_count=0,
                    max_retries=2,
                    is_resolved=False,
                    resolution_outcome="NONE"
                )
                self.db.add(new_case)

                audit = AuditEvent(
                    case_id=case_id,
                    event_type="DETECTED",
                    actor="SYSTEM_ENGINE",
                    is_simulated=True,
                    description=f"Detected abandoned cart of ${chk.amount_cents/100:.2f} ({chk.cart_items_count} items)",
                    metadata_json=json.dumps({"checkout_token": chk.checkout_token, "priority": label, "score": score})
                )
                self.db.add(audit)
                new_cases_count += 1

        self.db.commit()
        return new_cases_count

    def refresh_case_priority(self, case: RecoveryCase):
        """Recomputes priority based on current age, retry count, and failure reasons."""
        now = datetime.now(timezone.utc)
        created = case.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = max(0, (now - created).days)

        label, score, reasons = calculate_priority_score(
            amount_cents=case.amount_cents,
            source_type=case.source_type,
            age_days=age_days,
            retry_count=case.retry_count,
            failure_reason=case.failure_reason or ""
        )
        case.priority = label
        case.priority_score = score
        case.priority_reasons = json.dumps(reasons)
        self.db.commit()
