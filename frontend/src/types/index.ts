export interface Customer {
  id: number;
  customer_ref: string;
  name: string;
  email: string;
  phone?: string;
  created_at: string;
}

export interface CaseAction {
  id: string;
  case_id: string;
  action_type: string;
  is_simulated: boolean;
  idempotency_key: string;
  status: string;
  requires_approval: boolean;
  proposed_payload: string;
  execution_result: string;
  verification_status: string;
  verified_at?: string;
  error_message?: string;
  created_at: string;
  executed_at?: string;
}

export interface ApprovalRecord {
  id: string;
  action_id: string;
  case_id: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  reviewer: string;
  reason?: string;
  potential_consequence?: string;
  reviewed_at?: string;
  created_at: string;
  action?: CaseAction;
}

export interface RecoveryCase {
  id: string;
  source_type: 'failed_payment' | 'overdue_invoice' | 'abandoned_checkout';
  source_id: string;
  customer_id: number;
  amount_cents: number;
  currency: string;
  status: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  priority_score: number;
  priority_reasons: string;
  failure_reason?: string;
  recommended_action?: string;
  retry_count: number;
  max_retries: number;
  last_attempt_at?: string;
  cooldown_until?: string;
  is_resolved: boolean;
  resolution_outcome: string;
  recovered_at?: string;
  created_at: string;
  updated_at: string;
  customer?: Customer;
  actions: CaseAction[];
  approvals: ApprovalRecord[];
}

export interface DashboardSummary {
  revenue_at_risk_cents: number;
  eligible_recovery_cents: number;
  confirmed_live_recovered_cents: number;
  simulated_recovered_cents: number;
  open_cases_count: number;
  pending_approvals_count: number;
  revenue_at_risk_display: string;
  eligible_recovery_display: string;
  confirmed_live_recovered_display: string;
  simulated_recovered_display: string;
  recovery_success_rate_percent: number;
  recovery_denominator_explanation: string;
  cases_by_type: Record<string, number>;
  cases_by_priority: Record<string, number>;
  cases_by_status: Record<string, number>;
  recent_activity: Array<{
    id: string;
    event_type: string;
    actor: string;
    description: string;
    is_simulated: boolean;
    case_id?: string;
    created_at: string;
  }>;
  simulation_mode: boolean;
}

export interface AuditEvent {
  id: string;
  case_id?: string;
  action_id?: string;
  event_type: string;
  actor: string;
  is_simulated: boolean;
  description: string;
  metadata_json: string;
  created_at: string;
}

export interface IntegrationConnection {
  id: string;
  provider_name: string;
  provider_type: string;
  status: 'SIMULATED' | 'CONNECTED' | 'NOT_CONNECTED' | 'ERROR';
  description: string;
  last_sync_at?: string;
  settings_json: string;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  simulation_mode: boolean;
  database_ok: boolean;
  ollama_ok: boolean;
  ollama_model: string;
  ollama_details?: Record<string, any>;
}

export interface AgentToolCallInfo {
  tool_name: string;
  parameters: Record<string, any>;
  result: any;
}

export interface AgentChatResponse {
  reply: string;
  case_id?: string;
  tools_called: AgentToolCallInfo[];
  requires_approval: boolean;
  proposed_action_id?: string;
  source: string;
}

export interface ImportResult {
  record_type: string;
  total_rows: number;
  imported_rows: number;
  skipped_duplicates: number;
  error_count: number;
  errors: string[];
  new_cases_detected: number;
}

export interface BusinessAnomaly {
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
  action_recommended: string;
}

export interface BusinessCrawlResult {
  status: string;
  message: string;
  total_records_inspected: number;
  customers_imported: number;
  failed_payments_detected: number;
  overdue_invoices_detected: number;
  abandoned_checkouts_detected: number;
  total_loss_at_risk_display: string;
  anomalies_detected: BusinessAnomaly[];
  new_cases_created: number;
  ai_strategic_diagnosis: string;
}

export interface BusinessAuditSummary {
  total_recovery_cases: number;
  failed_payments_count: number;
  overdue_invoices_count: number;
  abandoned_checkouts_count: number;
  total_revenue_at_risk_cents: number;
  total_revenue_at_risk_display: string;
  qwen_strategic_diagnosis: string;
}
