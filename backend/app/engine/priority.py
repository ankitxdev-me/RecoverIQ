from typing import Tuple, List
import json

def calculate_priority_score(
    amount_cents: int,
    source_type: str,
    age_days: int,
    retry_count: int,
    failure_reason: str = ""
) -> Tuple[str, int, List[str]]:
    """
    Deterministic transparent priority scoring (0 - 100):
    Factors:
    - Amount factor (0 - 40 pts)
    - Age/Urgency factor (0 - 30 pts)
    - Recoverability factor (0 - 20 pts)
    - Customer engagement / failure severity factor (0 - 10 pts)
    
    Returns:
    (priority_label: CRITICAL|HIGH|MEDIUM|LOW, score: int, reasons: List[str])
    """
    score = 0
    reasons = []

    # 1. Amount Factor (up to 40 points)
    # Higher value cases represent greater revenue loss
    if amount_cents >= 250000:  # $2,500+
        score += 40
        reasons.append("High monetary value (>= $2,500.00): +40 pts")
    elif amount_cents >= 100000:  # $1,000+
        score += 30
        reasons.append("Significant monetary value (>= $1,000.00): +30 pts")
    elif amount_cents >= 25000:  # $250+
        score += 20
        reasons.append("Moderate monetary value (>= $250.00): +20 pts")
    else:
        score += 10
        reasons.append("Base monetary value (< $250.00): +10 pts")

    # 2. Age / Urgency Factor (up to 30 points)
    # Fresh failures/abandonments are most recoverable before interest wanes or debt hardens
    if source_type == "failed_payment":
        if age_days <= 2:
            score += 30
            reasons.append("Immediate failure (< 48 hrs) has highest recovery conversion: +30 pts")
        elif age_days <= 7:
            score += 20
            reasons.append("Recent failure (3-7 days old): +20 pts")
        else:
            score += 10
            reasons.append("Aging failure (> 7 days): +10 pts")

    elif source_type == "abandoned_checkout":
        if age_days <= 1:
            score += 30
            reasons.append("Fresh cart abandonment (within 24 hours): +30 pts")
        elif age_days <= 3:
            score += 20
            reasons.append("Recent cart abandonment (1-3 days): +20 pts")
        else:
            score += 5
            reasons.append("Older abandoned cart (> 3 days, decaying conversion): +5 pts")

    elif source_type == "overdue_invoice":
        if age_days >= 30:
            score += 30
            reasons.append("Severely overdue invoice (>= 30 days, high risk of default): +30 pts")
        elif age_days >= 14:
            score += 25
            reasons.append("Moderately overdue invoice (14-29 days): +25 pts")
        else:
            score += 15
            reasons.append("Recently overdue invoice (< 14 days): +15 pts")

    # 3. Recoverability / Retry Fatigue Factor (up to 20 points)
    if retry_count == 0:
        score += 20
        reasons.append("Unattempted case (first recovery attempt has top yield): +20 pts")
    elif retry_count == 1:
        score += 15
        reasons.append("Single prior attempt: +15 pts")
    elif retry_count == 2:
        score += 8
        reasons.append("Two prior attempts (approaching retry exhaustion): +8 pts")
    else:
        score += 0
        reasons.append("Maximum retry fatigue (low marginal return): +0 pts")

    # 4. Failure Reason Specifics (up to 10 points)
    reason_lower = (failure_reason or "").lower()
    if "insufficient_funds" in reason_lower:
        score += 10
        reasons.append("Soft decline (insufficient funds is highly recoverable with smart retry): +10 pts")
    elif "expired_card" in reason_lower:
        score += 8
        reasons.append("Card update required (recoverable via automated customer update link): +8 pts")
    elif "cart_abandoned" in reason_lower:
        score += 7
        reasons.append("Abandoned checkout intent (recoverable via targeted incentive): +7 pts")
    elif "fraud" in reason_lower or "stolen" in reason_lower:
        score = max(0, score - 30)
        reasons.append("Hard decline / fraud risk flag: -30 pts")

    # Clamp score between 0 and 100
    score = max(0, min(100, score))

    if score >= 80:
        label = "CRITICAL"
    elif score >= 60:
        label = "HIGH"
    elif score >= 40:
        label = "MEDIUM"
    else:
        label = "LOW"

    return label, score, reasons
