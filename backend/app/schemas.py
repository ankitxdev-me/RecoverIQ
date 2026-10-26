from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    customer_ref: str
    name: str
    email: str
    phone: Optional[str] = None

class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

# --- Recovery Case Schemas ---
class CaseActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    case_id: str
    action_type: str
    is_simulated: bool
    idempotency_key: str
    status: str
    requires_approval: bool
    proposed_payload: str
    execution_result: str
    verification_status: str
    verified_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    executed_at: Optional[datetime] = None

class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    action_id: str
    case_id: str
    status: str
    reviewer: str
    reason: Optional[str] = None
    potential_consequence: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    action: Optional[CaseActionResponse] = None

class RecoveryCaseBase(BaseModel):
    id: str
    source_type: str
    source_id: str
    customer_id: int
    amount_cents: int
    currency: str
    status: str
    priority: str
    priority_score: int
    priority_reasons: str
    failure_reason: Optional[str] = None
    recommended_action: Optional[str] = None
    retry_count: int
    max_retries: int
    is_resolved: bool
    resolution_outcome: str

class RecoveryCaseResponse(RecoveryCaseBase):
    model_config = ConfigDict(from_attributes=True)
    last_attempt_at: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    recovered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerResponse] = None
    actions: List[CaseActionResponse] = []
    approvals: List[ApprovalResponse] = []
    
    @property
    def amount_display(self) -> str:
        return f"${self.amount_cents / 100:,.2f}"

# --- Dashboard Summary Schemas ---
class DashboardSummaryResponse(BaseModel):
    revenue_at_risk_cents: int
    eligible_recovery_cents: int
    confirmed_live_recovered_cents: int
    simulated_recovered_cents: int
    open_cases_count: int
    pending_approvals_count: int
    
    revenue_at_risk_display: str
    eligible_recovery_display: str
    confirmed_live_recovered_display: str
    simulated_recovered_display: str
    
    recovery_success_rate_percent: float
    recovery_denominator_explanation: str
    
    cases_by_type: Dict[str, int]
    cases_by_priority: Dict[str, int]
    cases_by_status: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    simulation_mode: bool

# --- Action & Approval Requests ---
class ActionProposeRequest(BaseModel):
    case_id: str
    action_type: str
    is_simulated: bool = True
    payload: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVE|REJECT)$")
    reason: Optional[str] = None
    reviewer: str = "HUMAN_OPERATOR"

class ActionExecuteRequest(BaseModel):
    simulated_outcome: Optional[str] = None

class ActionVerifyRequest(BaseModel):
    verification_source: str = "simulated_provider"

# --- AI Chat / Agent Schemas ---
class AgentChatRequest(BaseModel):
    message: str
    case_id: Optional[str] = None

class AgentToolCallInfo(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    result: Any

class AgentChatResponse(BaseModel):
    reply: str
    case_id: Optional[str] = None
    tools_called: List[AgentToolCallInfo] = []
    requires_approval: bool = False
    proposed_action_id: Optional[str] = None
    source: str = "ollama_model"

# --- Audit Event Schemas ---
class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    case_id: Optional[str] = None
    action_id: Optional[str] = None
    event_type: str
    actor: str
    is_simulated: bool
    description: str
    metadata_json: str
    created_at: datetime

# --- Integration Status Schemas ---
class IntegrationStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    provider_name: str
    provider_type: str
    status: str
    description: str
    last_sync_at: Optional[datetime] = None
    settings_json: str

class SystemHealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    simulation_mode: bool
    database_ok: bool
    ollama_ok: bool
    ollama_model: str
    ollama_details: Optional[Dict[str, Any]] = None
