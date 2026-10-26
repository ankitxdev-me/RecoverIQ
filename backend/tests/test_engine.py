from datetime import datetime, timezone, timedelta
from backend.app.engine.priority import calculate_priority_score
from backend.app.engine.eligibility import is_eligible_for_recovery, determine_recommended_action

def test_priority_score_high_value_fresh_failure():
    label, score, reasons = calculate_priority_score(
        amount_cents=300000,  # $3,000.00
        source_type="failed_payment",
        age_days=1,
        retry_count=0,
        failure_reason="insufficient_funds"
    )
    # 40 (amount >= 2500) + 30 (fresh failure <= 2 days) + 20 (retry=0) + 10 (insufficient funds) = 100
    assert score == 100
    assert label == "CRITICAL"
    assert len(reasons) >= 4

def test_priority_score_low_value_exhausted():
    label, score, reasons = calculate_priority_score(
        amount_cents=5000,  # $50.00
        source_type="failed_payment",
        age_days=15,
        retry_count=3,
        failure_reason="card_declined"
    )
    # 10 (amount < 250) + 10 (age > 7) + 0 (exhausted retry) = 20
    assert score <= 30
    assert label == "LOW"

def test_eligibility_resolved_case_ineligible():
    eligible, reason = is_eligible_for_recovery(
        source_type="failed_payment",
        status="RECOVERED_LIVE",
        is_resolved=True,
        retry_count=1,
        max_retries=3,
        cooldown_until=None
    )
    assert eligible is False
    assert "resolved" in reason.lower()

def test_eligibility_cooldown_active():
    future_cooldown = datetime.now(timezone.utc) + timedelta(hours=5)
    eligible, reason = is_eligible_for_recovery(
        source_type="failed_payment",
        status="DETECTED",
        is_resolved=False,
        retry_count=1,
        max_retries=3,
        cooldown_until=future_cooldown
    )
    assert eligible is False
    assert "cooldown" in reason.lower()

def test_eligibility_retry_limit_exceeded():
    eligible, reason = is_eligible_for_recovery(
        source_type="failed_payment",
        status="DETECTED",
        is_resolved=False,
        retry_count=3,
        max_retries=3,
        cooldown_until=None
    )
    assert eligible is False
    assert "maximum retry limit" in reason.lower()

def test_abandoned_checkout_guardrail_never_charges_card():
    # Test that abandoned checkout NEVER recommends payment retry!
    action, requires_approval, explanation = determine_recommended_action(
        source_type="abandoned_checkout",
        failure_reason="cart_abandoned",
        retry_count=0,
        amount_cents=15000
    )
    assert "RETRY" not in action
    assert "PAYMENT_RETRY" not in action
    assert action in ("SEND_CART_REMINDER", "OFFER_CHECKOUT_INCENTIVE")
