import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Index, Enum
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_ref = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    email = Column(String(128), index=True, nullable=False)
    phone = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    transactions = relationship("Transaction", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    orders = relationship("Order", back_populates="customer")
    checkouts = relationship("Checkout", back_populates="customer")
    recovery_cases = relationship("RecoveryCase", back_populates="customer")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    external_id = Column(String(128), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    provider = Column(String(64), default="stripe_simulated")
    amount_cents = Column(Integer, nullable=False)  # Integer minor currency units (cents)
    currency = Column(String(3), default="USD")
    status = Column(String(32), nullable=False)  # FAILED, PENDING, SUCCEEDED, REFUNDED
    failure_code = Column(String(64), nullable=True)  # card_declined, insufficient_funds, expired_card
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    customer = relationship("Customer", back_populates="transactions")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_number = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)  # Integer minor units
    currency = Column(String(3), default="USD")
    status = Column(String(32), nullable=False)  # ISSUED, OVERDUE, PAID, VOID
    due_date = Column(DateTime(timezone=True), nullable=False)
    days_overdue = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    customer = relationship("Customer", back_populates="invoices")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_ref = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(32), nullable=False)  # PENDING, COMPLETED, CANCELLED
    created_at = Column(DateTime(timezone=True), default=utc_now)

    customer = relationship("Customer", back_populates="orders")


class Checkout(Base):
    __tablename__ = "checkouts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    checkout_token = Column(String(128), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    cart_items_count = Column(Integer, default=1)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(32), nullable=False)  # ABANDONED, RECOVERED, EXPIRED
    abandoned_at = Column(DateTime(timezone=True), default=utc_now)
    last_activity_at = Column(DateTime(timezone=True), default=utc_now)

    customer = relationship("Customer", back_populates="checkouts")


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(String(64), primary_key=True, index=True)  # e.g. CASE-PAY-1001
    source_type = Column(String(32), nullable=False, index=True)  # failed_payment, overdue_invoice, abandoned_checkout
    source_id = Column(String(128), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Lifecycle status:
    # DETECTED, INVESTIGATING, ACTION_REQUIRED, PENDING_APPROVAL, APPROVED, EXECUTING, VERIFYING, RECOVERED_LIVE, RECOVERED_SIMULATED, FAILED, STALE, CANCELLED
    status = Column(String(32), default="DETECTED", index=True, nullable=False)
    
    # Priority & scoring
    priority = Column(String(16), default="MEDIUM", index=True, nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    priority_score = Column(Integer, default=50)  # 0 to 100
    priority_reasons = Column(Text, default="[]")  # JSON array of reasons
    
    # Failure diagnostics & recovery recommendations
    failure_reason = Column(Text, nullable=True)
    recommended_action = Column(String(64), nullable=True)
    
    # Execution & guardrails
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    cooldown_until = Column(DateTime(timezone=True), nullable=True)
    
    # Outcomes
    is_resolved = Column(Boolean, default=False, index=True)
    resolution_outcome = Column(String(32), default="NONE")  # NONE, RECOVERED_LIVE, RECOVERED_SIMULATED, FAILED_PERMANENT, MANUALLY_CLOSED
    recovered_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    customer = relationship("Customer", back_populates="recovery_cases")
    actions = relationship("RecoveryAction", back_populates="case", cascade="all, delete-orphan")
    approvals = relationship("ApprovalRecord", back_populates="case", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_source_type_source_id", "source_type", "source_id", unique=True),
    )


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)  # SIMULATED_RETRY, SIMULATED_REMINDER, SIMULATED_DISCOUNT_OFFER, LIVE_PAYMENT_RETRY, LIVE_EMAIL_REMINDER
    is_simulated = Column(Boolean, default=True, nullable=False)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    
    # Action Status:
    # PROPOSED, PENDING_APPROVAL, APPROVED, REJECTED, EXECUTING, EXECUTED, VERIFIED_SUCCESS, VERIFIED_FAILURE, FAILED
    status = Column(String(32), default="PROPOSED", index=True, nullable=False)
    requires_approval = Column(Boolean, default=False)
    
    proposed_payload = Column(Text, default="{}")  # JSON
    execution_result = Column(Text, default="{}")  # JSON
    
    # Verification: UNVERIFIED, VERIFIED_CONFIRMED, VERIFIED_FAILED
    verification_status = Column(String(32), default="UNVERIFIED", index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    executed_at = Column(DateTime(timezone=True), nullable=True)

    case = relationship("RecoveryCase", back_populates="actions")
    approval = relationship("ApprovalRecord", back_populates="action", uselist=False, cascade="all, delete-orphan")


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    action_id = Column(String(64), ForeignKey("recovery_actions.id"), unique=True, nullable=False)
    case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    status = Column(String(32), default="PENDING", index=True, nullable=False)  # PENDING, APPROVED, REJECTED
    reviewer = Column(String(128), default="HUMAN_OPERATOR")
    reason = Column(Text, nullable=True)
    potential_consequence = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    action = relationship("RecoveryAction", back_populates="approval")
    case = relationship("RecoveryCase", back_populates="approvals")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    case_id = Column(String(64), nullable=True, index=True)
    action_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    actor = Column(String(64), nullable=False)  # SYSTEM_ENGINE, AI_AGENT, HUMAN_OPERATOR, SIMULATED_PROVIDER
    is_simulated = Column(Boolean, default=True)
    description = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)


class IntegrationConnection(Base):
    __tablename__ = "integration_connections"

    id = Column(String(64), primary_key=True)  # stripe_simulated, shopify_simulated, quickbooks_simulated, ollama_local
    provider_name = Column(String(64), nullable=False)
    provider_type = Column(String(64), nullable=False)  # payment_gateway, ecommerce_platform, accounting_system, ai_reasoning_engine
    status = Column(String(32), nullable=False)  # SIMULATED, CONNECTED, NOT_CONNECTED, ERROR
    description = Column(Text, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    settings_json = Column(Text, default="{}")
