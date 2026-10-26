import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.app.database import Base
from backend.app.models import Customer, RecoveryCase, RecoveryAction, ApprovalRecord
from backend.app.services.approval_service import ActionApprovalService

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test customer and case
    cust = Customer(customer_ref="CUST-TEST", name="Test Corp", email="test@corp.com")
    session.add(cust)
    session.flush()

    case = RecoveryCase(
        id="CASE-TEST-100",
        source_type="failed_payment",
        source_id="tx_test_100",
        customer_id=cust.id,
        amount_cents=120000,  # $1,200.00 (exceeds $500 approval threshold)
        currency="USD",
        status="DETECTED",
        priority="HIGH",
        priority_score=75,
        priority_reasons="[]",
        failure_reason="insufficient_funds",
        recommended_action="SIMULATED_PAYMENT_RETRY",
        retry_count=0,
        max_retries=3,
        is_resolved=False,
        resolution_outcome="NONE"
    )
    session.add(case)
    session.commit()

    yield session
    session.close()

def test_high_value_action_requires_approval(test_db):
    service = ActionApprovalService(test_db)
    action = service.propose_action(
        case_id="CASE-TEST-100",
        action_type="SIMULATED_PAYMENT_RETRY"
    )
    assert action.requires_approval is True
    assert action.status == "PENDING_APPROVAL"

    # Verify approval record created
    approval = test_db.query(ApprovalRecord).filter(ApprovalRecord.action_id == action.id).first()
    assert approval is not None
    assert approval.status == "PENDING"

def test_duplicate_active_action_rejected(test_db):
    service = ActionApprovalService(test_db)
    service.propose_action(case_id="CASE-TEST-100", action_type="SIMULATED_PAYMENT_RETRY")
    
    # Second attempt while first is pending must fail with 409
    with pytest.raises(HTTPException) as exc_info:
        service.propose_action(case_id="CASE-TEST-100", action_type="SIMULATED_PAYMENT_RETRY")
    assert exc_info.value.status_code == 409

def test_approve_then_execute_then_verify_flow(test_db):
    service = ActionApprovalService(test_db)
    action = service.propose_action(case_id="CASE-TEST-100", action_type="SIMULATED_PAYMENT_RETRY")
    
    # 1. Unapproved action cannot be executed
    with pytest.raises(HTTPException) as exc_info:
        service.execute_action(action.id)
    assert exc_info.value.status_code == 400

    # 2. Approve action
    approved_action = service.review_approval(action.id, decision="APPROVE", reviewer="SENIOR_MANAGER")
    assert approved_action.status == "APPROVED"

    # 3. Execute action
    executed_action = service.execute_action(action.id, simulated_outcome="SUCCESS")
    assert executed_action.status == "EXECUTED"
    
    # Check case is in VERIFYING state, NOT yet counted as recovered!
    case = test_db.query(RecoveryCase).filter(RecoveryCase.id == "CASE-TEST-100").first()
    assert case.status == "VERIFYING"
    assert case.is_resolved is False  # Must not count as recovered yet

    # 4. Explicit verification
    verified_act, verified_case = service.verify_action_outcome(action.id)
    assert verified_act.verification_status == "VERIFIED_CONFIRMED"
    assert verified_case.status == "RECOVERED_SIMULATED"
    assert verified_case.resolution_outcome == "RECOVERED_SIMULATED"
    assert verified_case.is_resolved is True

def test_reject_workflow(test_db):
    service = ActionApprovalService(test_db)
    action = service.propose_action(case_id="CASE-TEST-100", action_type="SIMULATED_PAYMENT_RETRY")
    
    rejected_action = service.review_approval(action.id, decision="REJECT", reviewer="AUDITOR", reason="Customer disputing charge")
    assert rejected_action.status == "REJECTED"
    
    case = test_db.query(RecoveryCase).filter(RecoveryCase.id == "CASE-TEST-100").first()
    assert case.status == "ACTION_REQUIRED"
