from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class ProviderTransactionResult(BaseModel):
    success: bool
    status: str  # SUCCEEDED, FAILED, PENDING
    transaction_reference: str
    amount_cents: int
    currency: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_simulated: bool = True
    provider_raw_response: Dict[str, Any] = {}
    timestamp: datetime

class ProviderMessageResult(BaseModel):
    success: bool
    status: str  # DELIVERED, FAILED, QUEUED
    message_reference: str
    recipient: str
    channel: str  # email, sms
    content_summary: str
    is_simulated: bool = True
    provider_raw_response: Dict[str, Any] = {}
    timestamp: datetime

class BasePaymentProvider(ABC):
    """
    Standard interface for payment gateways (e.g. Stripe, Adyen, Braintree).
    Future live providers must implement these methods.
    """
    @abstractmethod
    def retry_payment(self, transaction_id: str, amount_cents: int, currency: str, idempotency_key: str) -> ProviderTransactionResult:
        """Attempt to re-charge a failed transaction."""
        pass

    @abstractmethod
    def verify_payment_status(self, transaction_reference: str) -> ProviderTransactionResult:
        """Query the gateway for the verified transaction outcome."""
        pass


class BaseEcommerceProvider(ABC):
    """
    Standard interface for eCommerce platforms (e.g. Shopify, WooCommerce, Magento).
    """
    @abstractmethod
    def fetch_abandoned_checkouts(self, limit: int = 50) -> list:
        pass

    @abstractmethod
    def create_recovery_discount(self, checkout_token: str, discount_percent: int) -> Dict[str, Any]:
        pass


class BaseAccountingProvider(ABC):
    """
    Standard interface for accounting and invoicing (e.g. QuickBooks, Xero, NetSuite).
    """
    @abstractmethod
    def fetch_overdue_invoices(self, min_days_overdue: int = 1) -> list:
        pass

    @abstractmethod
    def record_invoice_payment(self, invoice_number: str, amount_cents: int, payment_ref: str) -> Dict[str, Any]:
        pass
