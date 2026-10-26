import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from backend.app.models import (
    Customer, Transaction, Invoice, Checkout, RecoveryCase, RecoveryAction, ApprovalRecord, AuditEvent
)
from backend.app.integrations.registry import seed_integrations_if_empty
from backend.app.engine.priority import calculate_priority_score
from backend.app.engine.eligibility import determine_recommended_action

def reset_and_seed_database(db: Session):
    """
    Clears all application data and re-seeds deterministic demo records.
    Ensures a pristine state for evaluation.
    """
    # Clear tables in safe order
    db.query(ApprovalRecord).delete()
    db.query(RecoveryAction).delete()
    db.query(AuditEvent).delete()
    db.query(RecoveryCase).delete()
    db.query(Transaction).delete()
    db.query(Invoice).delete()
    db.query(Checkout).delete()
    db.query(Customer).delete()
    db.commit()

    now = datetime.now(timezone.utc)

    # 1. Seed Integrations
    seed_integrations_if_empty(db)

    # 2. Seed Customers
    customers_data = [
        {"ref": "CUST-001", "name": "Acme Corporation", "email": "billing@acmecorp.com", "phone": "+1-555-0101"},
        {"ref": "CUST-002", "name": "Global Tech Logistics", "email": "finance@globaltechlog.com", "phone": "+1-555-0102"},
        {"ref": "CUST-003", "name": "Sarah Jenkins", "email": "sarah.j@example.com", "phone": "+1-555-0103"},
        {"ref": "CUST-004", "name": "Apex Dynamics", "email": "accounts@apexdynamics.io", "phone": "+1-555-0104"},
        {"ref": "CUST-005", "name": "Enterprise Cloud Inc", "email": "ap@enterprisecloud.net", "phone": "+1-555-0105"},
        {"ref": "CUST-006", "name": "Nexus Software", "email": "treasury@nexussoft.com", "phone": "+1-555-0106"},
        {"ref": "CUST-007", "name": "Horizon BioLabs", "email": "billing@horizonbiolabs.com", "phone": "+1-555-0107"}
    ]

    cust_objs = {}
    for c_data in customers_data:
        c = Customer(
            customer_ref=c_data["ref"],
            name=c_data["name"],
            email=c_data["email"],
            phone=c_data["phone"],
            created_at=now - timedelta(days=60)
        )
        db.add(c)
        db.flush()
        cust_objs[c_data["ref"]] = c

    # 3. Create Case 1: Failed Payment (Acme Corp, $1,450.00, Insufficient Funds - Ready for smart retry)
    tx1 = Transaction(
        external_id="tx_live_sim_1001",
        customer_id=cust_objs["CUST-001"].id,
        provider="stripe_simulated",
        amount_cents=145000,  # $1,450.00
        currency="USD",
        status="FAILED",
        failure_code="insufficient_funds",
        failure_reason="Customer card declined due to temporary insufficient funds.",
        created_at=now - timedelta(hours=14)
    )
    db.add(tx1)
    db.flush()

    p_label1, p_score1, p_reasons1 = calculate_priority_score(
        amount_cents=145000, source_type="failed_payment", age_days=0, retry_count=0, failure_reason="insufficient_funds"
    )
    rec_act1, req_app1, _ = determine_recommended_action(
        source_type="failed_payment", failure_reason="insufficient_funds", retry_count=0, amount_cents=145000
    )

    case1 = RecoveryCase(
        id="CASE-PAY-1001",
        source_type="failed_payment",
        source_id=tx1.external_id,
        customer_id=cust_objs["CUST-001"].id,
        amount_cents=145000,
        currency="USD",
        status="DETECTED",
        priority=p_label1,
        priority_score=p_score1,
        priority_reasons=json.dumps(p_reasons1),
        failure_reason="insufficient_funds",
        recommended_action=rec_act1,
        retry_count=0,
        max_retries=3,
        is_resolved=False,
        resolution_outcome="NONE",
        created_at=now - timedelta(hours=14)
    )
    db.add(case1)

    # 4. Create Case 2: Overdue Invoice (Global Tech, $3,200.00, 35 days overdue - High Urgency)
    inv2 = Invoice(
        invoice_number="INV-2026-8802",
        customer_id=cust_objs["CUST-002"].id,
        amount_cents=320000,  # $3,200.00
        currency="USD",
        status="OVERDUE",
        due_date=now - timedelta(days=35),
        days_overdue=35,
        created_at=now - timedelta(days=65)
    )
    db.add(inv2)
    db.flush()

    p_label2, p_score2, p_reasons2 = calculate_priority_score(
        amount_cents=320000, source_type="overdue_invoice", age_days=35, retry_count=0, failure_reason="overdue_35_days"
    )
    rec_act2, _, _ = determine_recommended_action(
        source_type="overdue_invoice", failure_reason="overdue_35_days", retry_count=0, amount_cents=320000
    )

    case2 = RecoveryCase(
        id="CASE-INV-2002",
        source_type="overdue_invoice",
        source_id=inv2.invoice_number,
        customer_id=cust_objs["CUST-002"].id,
        amount_cents=320000,
        currency="USD",
        status="DETECTED",
        priority=p_label2,
        priority_score=p_score2,
        priority_reasons=json.dumps(p_reasons2),
        failure_reason="Invoice overdue by 35 days",
        recommended_action=rec_act2,
        retry_count=0,
        max_retries=3,
        is_resolved=False,
        resolution_outcome="NONE",
        created_at=now - timedelta(days=35)
    )
    db.add(case2)

    # 5. Create Case 3: Abandoned Checkout (Sarah Jenkins, $349.00 - Safe recovery incentive)
    chk3 = Checkout(
        checkout_token="chk_tok_991823",
        customer_id=cust_objs["CUST-003"].id,
        cart_items_count=3,
        amount_cents=34900,  # $349.00
        currency="USD",
        status="ABANDONED",
        abandoned_at=now - timedelta(hours=6),
        last_activity_at=now - timedelta(hours=6)
    )
    db.add(chk3)
    db.flush()

    p_label3, p_score3, p_reasons3 = calculate_priority_score(
        amount_cents=34900, source_type="abandoned_checkout", age_days=0, retry_count=0, failure_reason="cart_abandoned"
    )
    rec_act3, _, _ = determine_recommended_action(
        source_type="abandoned_checkout", failure_reason="cart_abandoned", retry_count=0, amount_cents=34900
    )

    case3 = RecoveryCase(
        id="CASE-CHK-3003",
        source_type="abandoned_checkout",
        source_id=chk3.checkout_token,
        customer_id=cust_objs["CUST-003"].id,
        amount_cents=34900,
        currency="USD",
        status="DETECTED",
        priority=p_label3,
        priority_score=p_score3,
        priority_reasons=json.dumps(p_reasons3),
        failure_reason="Customer dropped off at checkout payment step",
        recommended_action=rec_act3,
        retry_count=0,
        max_retries=2,
        is_resolved=False,
        resolution_outcome="NONE",
        created_at=now - timedelta(hours=6)
    )
    db.add(case3)

    # 6. Create Case 4: Resolved Case (Apex Dynamics, $850.00 - Should NOT be retried)
    tx4 = Transaction(
        external_id="tx_resolved_4004",
        customer_id=cust_objs["CUST-004"].id,
        provider="stripe_simulated",
        amount_cents=85000,
        currency="USD",
        status="SUCCEEDED",
        created_at=now - timedelta(days=10)
    )
    db.add(tx4)
    db.flush()

    case4 = RecoveryCase(
        id="CASE-PAY-4004",
        source_type="failed_payment",
        source_id=tx4.external_id,
        customer_id=cust_objs["CUST-004"].id,
        amount_cents=85000,
        currency="USD",
        status="RECOVERED_LIVE",
        priority="LOW",
        priority_score=15,
        priority_reasons=json.dumps(["Case previously settled: live transaction confirmed"]),
        failure_reason="Resolved previously via customer card update",
        recommended_action="NONE",
        retry_count=1,
        max_retries=3,
        is_resolved=True,
        resolution_outcome="RECOVERED_LIVE",
        recovered_at=now - timedelta(days=2),
        created_at=now - timedelta(days=10)
    )
    db.add(case4)

    # 7. Create Case 5: Protected Action Requiring Approval (Enterprise Cloud, $12,500.00)
    tx5 = Transaction(
        external_id="tx_highval_5005",
        customer_id=cust_objs["CUST-005"].id,
        provider="stripe_simulated",
        amount_cents=1250000,  # $12,500.00
        currency="USD",
        status="FAILED",
        failure_code="temporary_card_decline",
        failure_reason="Corporate payment card hold flagged for balance limit review",
        created_at=now - timedelta(hours=18)
    )
    db.add(tx5)
    db.flush()

    p_label5, p_score5, p_reasons5 = calculate_priority_score(
        amount_cents=1250000, source_type="failed_payment", age_days=0, retry_count=0, failure_reason="temporary_card_decline"
    )

    case5 = RecoveryCase(
        id="CASE-PAY-5005",
        source_type="failed_payment",
        source_id=tx5.external_id,
        customer_id=cust_objs["CUST-005"].id,
        amount_cents=1250000,
        currency="USD",
        status="PENDING_APPROVAL",
        priority=p_label5,
        priority_score=p_score5,
        priority_reasons=json.dumps(p_reasons5),
        failure_reason="Corporate payment card hold flagged for balance limit review",
        recommended_action="SIMULATED_PAYMENT_RETRY",
        retry_count=0,
        max_retries=3,
        is_resolved=False,
        resolution_outcome="NONE",
        created_at=now - timedelta(hours=18)
    )
    db.add(case5)
    db.flush()

    # Pre-populate proposed action & approval record for Case 5
    act5 = RecoveryAction(
        id="ACT-HIGH-5005",
        case_id=case5.id,
        action_type="SIMULATED_PAYMENT_RETRY",
        is_simulated=True,
        idempotency_key="idem_CASE-PAY-5005_RETRY_1",
        status="PENDING_APPROVAL",
        requires_approval=True,
        proposed_payload=json.dumps({"retry_amount_cents": 1250000, "note": "High value recovery retry"}),
        verification_status="UNVERIFIED",
        created_at=now - timedelta(hours=2)
    )
    db.add(act5)
    db.flush()

    app5 = ApprovalRecord(
        id="APP-REV-5005",
        action_id=act5.id,
        case_id=case5.id,
        status="PENDING",
        reviewer="PENDING_HUMAN_REVIEW",
        reason="High monetary amount ($12,500.00) exceeds automatic execution threshold ($500.00).",
        potential_consequence="Triggering charge on corporate account without approval may cause merchant dispute.",
        created_at=now - timedelta(hours=2)
    )
    db.add(app5)

    # 8. Create Case 6: Simulated Success (Nexus Software, $720.00 - Verified Recovered Simulated)
    tx6 = Transaction(
        external_id="tx_nexus_6006",
        customer_id=cust_objs["CUST-006"].id,
        provider="stripe_simulated",
        amount_cents=72000,  # $720.00
        currency="USD",
        status="FAILED",
        failure_code="temporary_limit",
        failure_reason="Temporary daily bank limit reached",
        created_at=now - timedelta(days=2)
    )
    db.add(tx6)
    db.flush()

    case6 = RecoveryCase(
        id="CASE-PAY-6006",
        source_type="failed_payment",
        source_id=tx6.external_id,
        customer_id=cust_objs["CUST-006"].id,
        amount_cents=72000,
        currency="USD",
        status="RECOVERED_SIMULATED",
        priority="HIGH",
        priority_score=68,
        priority_reasons=json.dumps(["Recovered in simulated test sandbox"]),
        failure_reason="Temporary daily bank limit reached",
        recommended_action="SIMULATED_PAYMENT_RETRY",
        retry_count=1,
        max_retries=3,
        is_resolved=True,
        resolution_outcome="RECOVERED_SIMULATED",
        recovered_at=now - timedelta(hours=4),
        created_at=now - timedelta(days=2)
    )
    db.add(case6)
    db.flush()

    act6 = RecoveryAction(
        id="ACT-NEXUS-6006",
        case_id=case6.id,
        action_type="SIMULATED_PAYMENT_RETRY",
        is_simulated=True,
        idempotency_key="idem_CASE-PAY-6006_RETRY_1",
        status="VERIFIED_SUCCESS",
        requires_approval=True,
        proposed_payload=json.dumps({"amount_cents": 72000}),
        execution_result=json.dumps({
            "success": True,
            "status": "SUCCEEDED",
            "transaction_reference": "sim_ch_99210298",
            "is_simulated": True,
            "provider_raw_response": {"mode": "SIMULATION_SANDBOX", "auth": "AUTH_SIM_OK_9918"}
        }),
        verification_status="VERIFIED_CONFIRMED",
        verified_at=now - timedelta(hours=4),
        created_at=now - timedelta(hours=6),
        executed_at=now - timedelta(hours=5)
    )
    db.add(act6)

    # 9. Create Case 7: Failed / Expired Attempt (Horizon Labs, $580.00 - Pending next action)
    tx7 = Transaction(
        external_id="tx_horizon_7007",
        customer_id=cust_objs["CUST-007"].id,
        provider="stripe_simulated",
        amount_cents=58000,  # $580.00
        currency="USD",
        status="FAILED",
        failure_code="expired_card",
        failure_reason="Card expired on 10/25",
        created_at=now - timedelta(days=4)
    )
    db.add(tx7)
    db.flush()

    case7 = RecoveryCase(
        id="CASE-PAY-7007",
        source_type="failed_payment",
        source_id=tx7.external_id,
        customer_id=cust_objs["CUST-007"].id,
        amount_cents=58000,
        currency="USD",
        status="ACTION_REQUIRED",
        priority="HIGH",
        priority_score=62,
        priority_reasons=json.dumps(["Card expired, requires customer payment update link"]),
        failure_reason="expired_card",
        recommended_action="SEND_PAYMENT_LINK",
        retry_count=1,
        max_retries=3,
        last_attempt_at=now - timedelta(days=1),
        cooldown_until=now - timedelta(hours=2),  # Cooldown finished
        is_resolved=False,
        resolution_outcome="NONE",
        created_at=now - timedelta(days=4)
    )
    db.add(case7)
    db.flush()

    act7 = RecoveryAction(
        id="ACT-HORIZON-7007",
        case_id=case7.id,
        action_type="SIMULATED_PAYMENT_RETRY",
        is_simulated=True,
        idempotency_key="idem_CASE-PAY-7007_RETRY_1",
        status="VERIFIED_FAILURE",
        requires_approval=False,
        proposed_payload=json.dumps({"amount_cents": 58000}),
        execution_result=json.dumps({
            "success": False,
            "status": "FAILED",
            "error_code": "expired_card",
            "error_message": "Card declined: Card expiration date has passed.",
            "is_simulated": True
        }),
        verification_status="VERIFIED_FAILED",
        error_message="Card declined: Card expiration date has passed.",
        verified_at=now - timedelta(days=1),
        created_at=now - timedelta(days=2),
        executed_at=now - timedelta(days=1)
    )
    db.add(act7)

    # 10. Audit History
    audit_entries = [
        {"type": "DETECTED", "actor": "SYSTEM_ENGINE", "case": "CASE-PAY-1001", "desc": "Detected failed payment of $1,450.00 (insufficient_funds)"},
        {"type": "DETECTED", "actor": "SYSTEM_ENGINE", "case": "CASE-INV-2002", "desc": "Detected overdue invoice INV-2026-8802 of $3,200.00 (35 days overdue)"},
        {"type": "DETECTED", "actor": "SYSTEM_ENGINE", "case": "CASE-CHK-3003", "desc": "Detected abandoned cart of $349.00 (3 items)"},
        {"type": "APPROVAL_REQUESTED", "actor": "AI_AGENT", "case": "CASE-PAY-5005", "desc": "High-value action ($12,500.00) routed to human approval queue"},
        {"type": "ACTION_EXECUTED", "actor": "SIMULATED_PROVIDER", "case": "CASE-PAY-6006", "desc": "Executed simulated retry for $720.00"},
        {"type": "ACTION_VERIFIED", "actor": "SYSTEM_ENGINE", "case": "CASE-PAY-6006", "desc": "Verified simulated recovery receipt: $720.00 confirmed in sandbox"},
        {"type": "ACTION_FAILED", "actor": "SIMULATED_PROVIDER", "case": "CASE-PAY-7007", "desc": "Simulated retry failed: Card declined (expired_card)"}
    ]

    for a in audit_entries:
        evt = AuditEvent(
            case_id=a["case"],
            event_type=a["type"],
            actor=a["actor"],
            is_simulated=True,
            description=a["desc"],
            created_at=now - timedelta(minutes=45)
        )
        db.add(evt)

    db.commit()
