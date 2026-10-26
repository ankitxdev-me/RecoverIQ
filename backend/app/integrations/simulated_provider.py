import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from backend.app.integrations.base import (
    BasePaymentProvider, ProviderTransactionResult, ProviderMessageResult
)

class SimulatedPaymentProvider(BasePaymentProvider):
    """
    Deterministic simulated payment gateway for demo and hackathon validation.
    Every output is explicitly flagged with is_simulated=True.
    Never connects to or charges real accounts.
    """

    def __init__(self, default_outcome: str = "SUCCESS"):
        self.default_outcome = default_outcome

    def retry_payment(
        self,
        transaction_id: str,
        amount_cents: int,
        currency: str,
        idempotency_key: str,
        forced_outcome: Optional[str] = None
    ) -> ProviderTransactionResult:
        now = datetime.now(timezone.utc)
        outcome = (forced_outcome or self.default_outcome).upper()
        sim_ref = f"sim_ch_{uuid.uuid4().hex[:12]}"

        if outcome == "SUCCESS":
            return ProviderTransactionResult(
                success=True,
                status="SUCCEEDED",
                transaction_reference=sim_ref,
                amount_cents=amount_cents,
                currency=currency,
                is_simulated=True,
                provider_raw_response={
                    "gateway": "Simulated Gateway v1.0",
                    "mode": "SIMULATION_SANDBOX",
                    "idempotency_key": idempotency_key,
                    "simulated_authorization_code": "AUTH_SIM_OK_9918",
                    "risk_score": 12,
                    "notice": "SIMULATION ONLY - NO REAL MONEY WAS TRANSFERRED"
                },
                timestamp=now
            )
        elif outcome in ("INSUFFICIENT_FUNDS", "FAILURE"):
            return ProviderTransactionResult(
                success=False,
                status="FAILED",
                transaction_reference=sim_ref,
                amount_cents=amount_cents,
                currency=currency,
                error_code="insufficient_funds",
                error_message="Card declined: Account balance insufficient to cover transaction amount.",
                is_simulated=True,
                provider_raw_response={
                    "gateway": "Simulated Gateway v1.0",
                    "mode": "SIMULATION_SANDBOX",
                    "decline_code": "insufficient_funds"
                },
                timestamp=now
            )
        elif outcome == "CARD_EXPIRED":
            return ProviderTransactionResult(
                success=False,
                status="FAILED",
                transaction_reference=sim_ref,
                amount_cents=amount_cents,
                currency=currency,
                error_code="expired_card",
                error_message="Card declined: Card expiration date has passed.",
                is_simulated=True,
                provider_raw_response={
                    "gateway": "Simulated Gateway v1.0",
                    "mode": "SIMULATION_SANDBOX",
                    "decline_code": "expired_card"
                },
                timestamp=now
            )
        else:
            return ProviderTransactionResult(
                success=False,
                status="PENDING",
                transaction_reference=sim_ref,
                amount_cents=amount_cents,
                currency=currency,
                error_code="gateway_processing",
                error_message="Simulated transaction queued for asynchronous clearance.",
                is_simulated=True,
                provider_raw_response={"mode": "SIMULATION_SANDBOX", "status": "pending_settlement"},
                timestamp=now
            )

    def verify_payment_status(self, transaction_reference: str) -> ProviderTransactionResult:
        now = datetime.now(timezone.utc)
        # In simulation mode, verify that the simulated charge is valid
        is_valid = transaction_reference.startswith("sim_ch_")
        return ProviderTransactionResult(
            success=is_valid,
            status="SUCCEEDED" if is_valid else "FAILED",
            transaction_reference=transaction_reference,
            amount_cents=0,
            currency="USD",
            is_simulated=True,
            provider_raw_response={
                "gateway": "Simulated Gateway v1.0",
                "verified": is_valid,
                "verification_mechanism": "cryptographic_sim_receipt_audit"
            },
            timestamp=now
        )


class SimulatedCommunicationProvider:
    """
    Simulates sending emails, SMS reminders, and discount incentives.
    Guarantees no real communications leave the sandbox.
    """
    def send_simulated_reminder(
        self,
        recipient: str,
        subject: str,
        body: str,
        channel: str = "email"
    ) -> ProviderMessageResult:
        now = datetime.now(timezone.utc)
        msg_ref = f"sim_msg_{uuid.uuid4().hex[:10]}"
        return ProviderMessageResult(
            success=True,
            status="DELIVERED",
            message_reference=msg_ref,
            recipient=recipient,
            channel=channel,
            content_summary=subject,
            is_simulated=True,
            provider_raw_response={
                "channel": channel,
                "sandbox": True,
                "delivered_to": recipient,
                "subject": subject,
                "preview": body[:120] + ("..." if len(body) > 120 else ""),
                "notice": "SIMULATION ONLY - NO REAL EMAIL/SMS WAS SENT"
            },
            timestamp=now
        )
