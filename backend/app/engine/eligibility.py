from datetime import datetime, timezone
from typing import Tuple, Optional

def is_eligible_for_recovery(
    source_type: str,
    status: str,
    is_resolved: bool,
    retry_count: int,
    max_retries: int,
    cooldown_until: Optional[datetime],
    failure_reason: str = ""
) -> Tuple[bool, str]:
    """
    Evaluates whether a recovery case is currently eligible for an action.
    Returns (eligible: bool, reason_detail: str).
    """
    if is_resolved:
        return False, "Case is already marked as resolved."

    if status in ("RECOVERED_LIVE", "RECOVERED_SIMULATED", "FAILED", "CANCELLED", "STALE"):
        return False, f"Case status '{status}' is non-actionable."

    if retry_count >= max_retries:
        return False, f"Maximum retry limit ({max_retries}) reached."

    # Check cooldown
    if cooldown_until:
        now = datetime.now(timezone.utc)
        cd = cooldown_until if cooldown_until.tzinfo is not None else cooldown_until.replace(tzinfo=timezone.utc)
        if cd > now:
            remaining_mins = int((cd - now).total_seconds() / 60)
            return False, f"Case is under cooldown. {remaining_mins} minutes remaining."

    # Failure code hard declines
    reason_lower = (failure_reason or "").lower()
    if "fraud" in reason_lower or "stolen" in reason_lower:
        return False, "Case involves suspected fraud or reported stolen card; automated recovery prohibited."

    if source_type == "abandoned_checkout" and "payment_retried" in reason_lower:
        return False, "Abandoned checkout cannot be charged directly without customer checkout completion."

    return True, "Case is eligible for recovery workflow."


def determine_recommended_action(
    source_type: str,
    failure_reason: str,
    retry_count: int,
    amount_cents: int
) -> Tuple[str, bool, str]:
    """
    Returns:
    (action_type: str, requires_approval: bool, explanation: str)
    
    Protected actions or high-value amounts require human approval!
    """
    reason_lower = (failure_reason or "").lower()
    is_high_value = amount_cents >= 50000  # >= $500.00

    if source_type == "failed_payment":
        if "insufficient_funds" in reason_lower or "temporary" in reason_lower:
            action = "SIMULATED_PAYMENT_RETRY"
            # High amount or 2nd/3rd retry requires approval
            requires_approval = is_high_value or (retry_count >= 1)
            explanation = (
                f"Smart retry scheduled for soft decline ('{failure_reason}'). "
                f"{'Requires human approval due to high balance or repeated attempt.' if requires_approval else 'Eligible for automated retry.'}"
            )
            return action, requires_approval, explanation

        elif "expired" in reason_lower or "invalid_card" in reason_lower:
            action = "SEND_PAYMENT_LINK"
            requires_approval = False
            explanation = "Customer card is expired/invalid; recommend sending a secure update link."
            return action, requires_approval, explanation

        else:
            action = "SEND_POLITE_REMINDER"
            requires_approval = is_high_value
            explanation = f"General failure ('{failure_reason}'); recommend customer notification."
            return action, requires_approval, explanation

    elif source_type == "overdue_invoice":
        if retry_count == 0:
            action = "SEND_POLITE_REMINDER"
            requires_approval = False
            explanation = "Initial overdue invoice notice with payment link."
            return action, requires_approval, explanation
        elif retry_count == 1:
            action = "SEND_URGENT_DEMAND"
            requires_approval = is_high_value
            explanation = "Second escalation reminder with clear due-date warning."
            return action, requires_approval, explanation
        else:
            action = "SCHEDULE_ACCOUNT_REVIEW"
            requires_approval = True
            explanation = "Multiple uncollected notices; human account review required before collection referral."
            return action, requires_approval, explanation

    elif source_type == "abandoned_checkout":
        # CRITICAL SAFETY: NEVER RETRY PAYMENT FOR ABANDONED CHECKOUT!
        if retry_count == 0:
            action = "SEND_CART_REMINDER"
            requires_approval = False
            explanation = "Friendly reminder with saved cart contents link."
            return action, requires_approval, explanation
        else:
            action = "OFFER_CHECKOUT_INCENTIVE"
            requires_approval = True  # Discounts/incentives require supervisor approval
            explanation = "Special recovery incentive (e.g. 10% coupon or free shipping) requiring approval."
            return action, requires_approval, explanation

    return "MANUAL_INVESTIGATION", True, "Unrecognized source pattern requires manual review."
