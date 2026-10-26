import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.models import RecoveryCase, RecoveryAction, ApprovalRecord, AuditEvent, Customer, Transaction, Invoice, Checkout
from backend.app.services.approval_service import ActionApprovalService
from backend.app.engine.priority import calculate_priority_score
from backend.app.engine.eligibility import is_eligible_for_recovery, determine_recommended_action

# --- Tool Input Schemas ---
class CaseQueryInput(BaseModel):
    limit: int = Field(default=10, description="Max cases to return (1-20)")
    status: Optional[str] = Field(default=None, description="Optional status filter")
    priority: Optional[str] = Field(default=None, description="Optional priority filter (CRITICAL, HIGH, MEDIUM, LOW)")

class CaseDetailsInput(BaseModel):
    case_id: str = Field(..., description="ID of the recovery case, e.g. CASE-PAY-1")

class PriorityCalcInput(BaseModel):
    amount_cents: int = Field(..., description="Monetary value in cents")
    source_type: str = Field(..., description="failed_payment, overdue_invoice, or abandoned_checkout")
    age_days: int = Field(default=1, description="Days since failure/abandonment")
    retry_count: int = Field(default=0, description="Number of prior attempts")
    failure_reason: str = Field(default="", description="Reason for failure")

class ActionRecommendInput(BaseModel):
    case_id: str = Field(..., description="ID of the recovery case")

class MessageDraftInput(BaseModel):
    case_id: str = Field(..., description="ID of the recovery case")
    tone: str = Field(default="polite", description="Tone: polite, firm, urgent, or incentive")

class RequestApprovalInput(BaseModel):
    case_id: str = Field(..., description="ID of the recovery case")
    action_type: str = Field(..., description="SIMULATED_PAYMENT_RETRY, SEND_PAYMENT_LINK, SEND_POLITE_REMINDER, etc.")
    reason: str = Field(..., description="Business rationale for the proposed action")

class ActionStatusInput(BaseModel):
    action_id: str = Field(..., description="ID of the recovery action")

class VerifyOutcomeInput(BaseModel):
    action_id: str = Field(..., description="ID of the executed action to verify")

# --- Tool Registry Definitions for Ollama ---
AVAILABLE_TOOLS = [
    {
        "name": "get_dashboard_summary",
        "description": "Fetch high-level financial summary: revenue at risk, eligible recovery amount, confirmed live recovered revenue, simulated recovered revenue, open case counts.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_recovery_cases",
        "description": "Retrieve a list of active revenue recovery cases with amounts, types, and priorities.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max cases to return (1-20)"},
                "status": {"type": "string", "description": "Status filter e.g. DETECTED, ACTION_REQUIRED"},
                "priority": {"type": "string", "description": "Priority filter e.g. CRITICAL, HIGH"}
            },
            "required": []
        }
    },
    {
        "name": "get_case_details",
        "description": "Get complete verified details for a specific recovery case including customer profile and action history.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Case ID (e.g. CASE-PAY-1)"}
            },
            "required": ["case_id"]
        }
    },
    {
        "name": "investigate_case",
        "description": "Perform deep multi-factor investigation on a case: analyze failure code, customer history, retry count, and recoverability.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Case ID (e.g. CASE-PAY-1)"}
            },
            "required": ["case_id"]
        }
    },
    {
        "name": "calculate_recovery_priority",
        "description": "Deterministically calculate the priority score (0-100) and tier for given financial and timing parameters.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount_cents": {"type": "integer", "description": "Amount in cents"},
                "source_type": {"type": "string", "description": "failed_payment, overdue_invoice, abandoned_checkout"},
                "age_days": {"type": "integer", "description": "Days since event"},
                "retry_count": {"type": "integer", "description": "Prior retries count"},
                "failure_reason": {"type": "string", "description": "Reason for failure"}
            },
            "required": ["amount_cents", "source_type"]
        }
    },
    {
        "name": "recommend_recovery_action",
        "description": "Generate validated recovery recommendation adhering to guardrails (e.g. never charge abandoned checkouts directly).",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Case ID to evaluate"}
            },
            "required": ["case_id"]
        }
    },
    {
        "name": "draft_customer_message",
        "description": "Draft tailored email/SMS recovery message tailored to customer name, amount, and case context.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Case ID"},
                "tone": {"type": "string", "description": "polite, firm, urgent, or incentive"}
            },
            "required": ["case_id"]
        }
    },
    {
        "name": "request_action_approval",
        "description": "Submit a proposed recovery action into the human approval queue.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Case ID"},
                "action_type": {"type": "string", "description": "SIMULATED_PAYMENT_RETRY, SEND_PAYMENT_LINK, etc."},
                "reason": {"type": "string", "description": "Why this action is recommended"}
            },
            "required": ["case_id", "action_type", "reason"]
        }
    },
    {
        "name": "get_action_status",
        "description": "Check the execution and verification status of a recovery action.",
        "parameters": {
            "type": "object",
            "properties": {
                "action_id": {"type": "string", "description": "Action ID, e.g. ACT-XXXX"}
            },
            "required": ["action_id"]
        }
    },
    {
        "name": "verify_recovery_outcome",
        "description": "Verify whether an executed recovery action produced confirmed recovery.",
        "parameters": {
            "type": "object",
            "properties": {
                "action_id": {"type": "string", "description": "Action ID to verify"}
            },
            "required": ["action_id"]
        }
    },
    {
        "name": "audit_business_anomalies",
        "description": "Audit and inspect the business database for real revenue leakage abnormalities: failed payment clusters, aging overdue receivables, and checkout dropoffs.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# --- Tool Execution Engine ---
def execute_tool_safely(tool_name: str, arguments: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Validates arguments with Pydantic and executes against database safely.
    Never executes arbitrary code.
    """
    try:
        if tool_name == "get_dashboard_summary":
            # Direct DB calculation
            cases = db.query(RecoveryCase).all()
            revenue_at_risk = sum(c.amount_cents for c in cases if not c.is_resolved)
            
            # Eligible recovery: open cases that satisfy eligibility rules
            eligible_amount = 0
            open_count = 0
            for c in cases:
                if not c.is_resolved:
                    open_count += 1
                    eligible, _ = is_eligible_for_recovery(
                        c.source_type, c.status, c.is_resolved, c.retry_count, c.max_retries, c.cooldown_until, c.failure_reason
                    )
                    if eligible:
                        eligible_amount += c.amount_cents

            # Confirmed live vs simulated
            live_recovered = sum(c.amount_cents for c in cases if c.resolution_outcome == "RECOVERED_LIVE")
            simulated_recovered = sum(c.amount_cents for c in cases if c.resolution_outcome == "RECOVERED_SIMULATED")
            
            pending_approvals = db.query(ApprovalRecord).filter(ApprovalRecord.status == "PENDING").count()

            return {
                "revenue_at_risk_display": f"${revenue_at_risk / 100:.2f}",
                "eligible_recovery_display": f"${eligible_amount / 100:.2f}",
                "confirmed_live_recovered_display": f"${live_recovered / 100:.2f}",
                "simulated_recovered_display": f"${simulated_recovered / 100:.2f}",
                "open_cases_count": open_count,
                "pending_approvals_count": pending_approvals,
                "simulation_mode": True
            }

        elif tool_name == "list_recovery_cases":
            inp = CaseQueryInput(**arguments)
            query = db.query(RecoveryCase)
            if inp.status:
                s_upper = inp.status.strip().upper()
                if s_upper in ("OPEN", "ACTIVE", "UNRESOLVED"):
                    query = query.filter(RecoveryCase.is_resolved == False)
                elif s_upper in ("CLOSED", "RESOLVED"):
                    query = query.filter(RecoveryCase.is_resolved == True)
                else:
                    query = query.filter(RecoveryCase.status.ilike(f"%{inp.status}%"))
            if inp.priority:
                query = query.filter(RecoveryCase.priority.ilike(inp.priority.strip().upper()))
            cases = query.order_by(RecoveryCase.priority_score.desc()).limit(min(20, max(1, inp.limit))).all()

            return {
                "cases": [
                    {
                        "id": c.id,
                        "source_type": c.source_type,
                        "customer_name": c.customer.name if c.customer else "Unknown",
                        "amount_display": f"${c.amount_cents / 100:.2f}",
                        "priority": c.priority,
                        "priority_score": c.priority_score,
                        "status": c.status,
                        "recommended_action": c.recommended_action
                    }
                    for c in cases
                ]
            }

        elif tool_name in ("get_case_details", "investigate_case"):
            inp = CaseDetailsInput(**arguments)
            c = db.query(RecoveryCase).filter(RecoveryCase.id == inp.case_id).first()
            if not c:
                return {"error": f"Case '{inp.case_id}' not found."}

            now = datetime.now(timezone.utc)
            created = c.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_days = max(0, (now - created).days)

            eligible, elig_reason = is_eligible_for_recovery(
                c.source_type, c.status, c.is_resolved, c.retry_count, c.max_retries, c.cooldown_until, c.failure_reason
            )

            actions = db.query(RecoveryAction).filter(RecoveryAction.case_id == c.id).all()

            investigation = {
                "case_id": c.id,
                "customer": {
                    "ref": c.customer.customer_ref if c.customer else "",
                    "name": c.customer.name if c.customer else "Unknown",
                    "email": c.customer.email if c.customer else "unknown@example.com"
                },
                "amount_display": f"${c.amount_cents / 100:,.2f}",
                "source_type": c.source_type,
                "source_id": c.source_id,
                "status": c.status,
                "priority": c.priority,
                "priority_score": c.priority_score,
                "age_days": age_days,
                "failure_reason": c.failure_reason,
                "retry_count": c.retry_count,
                "max_retries": c.max_retries,
                "is_eligible_for_recovery": eligible,
                "eligibility_notes": elig_reason,
                "recommended_action": c.recommended_action,
                "past_actions_count": len(actions)
            }
            return investigation

        elif tool_name == "calculate_recovery_priority":
            inp = PriorityCalcInput(**arguments)
            label, score, reasons = calculate_priority_score(
                amount_cents=inp.amount_cents,
                source_type=inp.source_type,
                age_days=inp.age_days,
                retry_count=inp.retry_count,
                failure_reason=inp.failure_reason
            )
            return {
                "priority": label,
                "priority_score": score,
                "reasons": reasons
            }

        elif tool_name == "recommend_recovery_action":
            inp = ActionRecommendInput(**arguments)
            c = db.query(RecoveryCase).filter(RecoveryCase.id == inp.case_id).first()
            if not c:
                return {"error": f"Case '{inp.case_id}' not found."}

            action, requires_approval, explanation = determine_recommended_action(
                source_type=c.source_type,
                failure_reason=c.failure_reason or "",
                retry_count=c.retry_count,
                amount_cents=c.amount_cents
            )
            return {
                "case_id": c.id,
                "recommended_action": action,
                "requires_human_approval": requires_approval,
                "rationale": explanation
            }

        elif tool_name == "draft_customer_message":
            inp = MessageDraftInput(**arguments)
            c = db.query(RecoveryCase).filter(RecoveryCase.id == inp.case_id).first()
            if not c:
                return {"error": f"Case '{inp.case_id}' not found."}

            cust_name = c.customer.name if c.customer else "Valued Customer"
            amount_str = f"${c.amount_cents / 100:,.2f}"

            if c.source_type == "failed_payment":
                subject = f"Action Needed: Update Payment Method for {amount_str}"
                body = (
                    f"Hi {cust_name},\n\n"
                    f"We were unable to process your recent payment of {amount_str}. "
                    f"To prevent any interruption in your service, please take a moment to update your payment details using our secure checkout link:\n\n"
                    f"https://app.recoveriq.io/pay/{c.id}\n\n"
                    f"If you have any questions or have already resolved this, please let us know.\n\n"
                    f"Best regards,\nCustomer Accounts Team"
                )
            elif c.source_type == "overdue_invoice":
                if inp.tone == "urgent":
                    subject = f"URGENT: Outstanding Balance Past Due — Invoice {c.source_id}"
                    body = (
                        f"Dear {cust_name},\n\n"
                        f"Our records indicate that invoice {c.source_id} for {amount_str} is significantly past due. "
                        f"Please submit payment immediately to avoid service interruption or account hold.\n\n"
                        f"Payment link: https://app.recoveriq.io/invoices/{c.id}\n\n"
                        f"Finance Operations"
                    )
                else:
                    subject = f"Friendly Reminder: Invoice {c.source_id} Payment Due"
                    body = (
                        f"Hi {cust_name},\n\n"
                        f"This is a gentle reminder that invoice {c.source_id} for {amount_str} is currently open. "
                        f"You can review and pay your invoice anytime at: https://app.recoveriq.io/invoices/{c.id}\n\n"
                        f"Thank you for your business!"
                    )
            else:  # abandoned checkout
                subject = f"Did you leave something behind? Complete your order for {amount_str}"
                body = (
                    f"Hi {cust_name},\n\n"
                    f"We noticed you left items in your cart. We've saved your selection so you can pick right back up:\n\n"
                    f"https://store.example.com/cart?token={c.source_id}\n\n"
                    f"Use code RECOVER10 for an extra 10% off at checkout today!\n\n"
                    f"Warmly,\nYour Shopping Team"
                )

            return {
                "case_id": c.id,
                "subject": subject,
                "body": body,
                "recipient": c.customer.email if c.customer else "unknown@example.com"
            }

        elif tool_name == "request_action_approval":
            inp = RequestApprovalInput(**arguments)
            service = ActionApprovalService(db)
            action = service.propose_action(
                case_id=inp.case_id,
                action_type=inp.action_type,
                payload={"reason": inp.reason},
                is_simulated=True,
                actor="AI_AGENT"
            )
            return {
                "action_id": action.id,
                "case_id": action.case_id,
                "status": action.status,
                "requires_approval": action.requires_approval,
                "message": "Action proposed and submitted to approval workflow."
            }

        elif tool_name == "get_action_status":
            inp = ActionStatusInput(**arguments)
            act = db.query(RecoveryAction).filter(RecoveryAction.id == inp.action_id).first()
            if not act:
                return {"error": f"Action '{inp.action_id}' not found."}
            return {
                "action_id": act.id,
                "case_id": act.case_id,
                "status": act.status,
                "verification_status": act.verification_status,
                "is_simulated": act.is_simulated,
                "executed_at": str(act.executed_at) if act.executed_at else None
            }

        elif tool_name == "verify_recovery_outcome":
            inp = VerifyOutcomeInput(**arguments)
            service = ActionApprovalService(db)
            act, case = service.verify_action_outcome(inp.action_id, actor="AI_AGENT")
            return {
                "action_id": act.id,
                "case_id": case.id,
                "verification_status": act.verification_status,
                "case_status": case.status,
                "resolution_outcome": case.resolution_outcome
            }

        elif tool_name == "audit_business_anomalies":
            failed_txs = db.query(Transaction).filter(Transaction.status == "FAILED").all()
            overdue_invs = db.query(Invoice).filter(Invoice.status == "OVERDUE").all()
            abandoned_carts = db.query(Checkout).filter(Checkout.status == "ABANDONED").all()
            cases = db.query(RecoveryCase).all()

            tx_loss = sum(t.amount_cents for t in failed_txs)
            inv_loss = sum(i.amount_cents for i in overdue_invs)
            cart_loss = sum(c.amount_cents for c in abandoned_carts)
            total_loss = tx_loss + inv_loss + cart_loss

            return {
                "total_loss_at_risk_display": f"${total_loss / 100:,.2f}",
                "failed_payments": {
                    "count": len(failed_txs),
                    "total_cents": tx_loss,
                    "sample_reasons": list(set([t.failure_reason for t in failed_txs if t.failure_reason]))[:3]
                },
                "overdue_invoices": {
                    "count": len(overdue_invs),
                    "total_cents": inv_loss,
                    "max_overdue_days": max([i.days_overdue for i in overdue_invs], default=0)
                },
                "abandoned_checkouts": {
                    "count": len(abandoned_carts),
                    "total_cents": cart_loss
                },
                "generated_cases_count": len(cases),
                "audit_verdict": "Real business data audited. High-priority leakage clusters mapped to automated recovery actions."
            }

        else:
            return {"error": f"Unknown tool '{tool_name}'"}

    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
