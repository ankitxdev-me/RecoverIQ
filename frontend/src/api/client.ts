import {
  DashboardSummary,
  RecoveryCase,
  CaseAction,
  ApprovalRecord,
  AuditEvent,
  IntegrationConnection,
  SystemHealth,
  AgentChatResponse,
  ImportResult,
  BusinessCrawlResult,
  BusinessAuditSummary,
} from '../types';

const BASE_URL = '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });

  if (!resp.ok) {
    let errorDetail = `Request failed: ${resp.status} ${resp.statusText}`;
    try {
      const err = await resp.json();
      if (err.detail) errorDetail = err.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return resp.json();
}

export const api = {
  // Health
  getHealth: () => fetchJson<SystemHealth>(`${BASE_URL}/api/health`),
  getOllamaDiagnostics: () => fetchJson<any>(`${BASE_URL}/api/health/ollama`),

  // Dashboard
  getDashboardSummary: () => fetchJson<DashboardSummary>(`${BASE_URL}/api/dashboard/summary`),

  // Cases
  getCases: (params?: {
    search?: string;
    source_type?: string;
    status?: string;
    priority?: string;
    is_resolved?: boolean;
    sort_by?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.source_type) q.append('source_type', params.source_type);
    if (params?.status) q.append('status', params.status);
    if (params?.priority) q.append('priority', params.priority);
    if (params?.is_resolved !== undefined) q.append('is_resolved', String(params.is_resolved));
    if (params?.sort_by) q.append('sort_by', params.sort_by);
    return fetchJson<RecoveryCase[]>(`${BASE_URL}/api/cases?${q.toString()}`);
  },

  getCaseById: (caseId: string) => fetchJson<RecoveryCase>(`${BASE_URL}/api/cases/${caseId}`),

  // Actions
  proposeAction: (data: { case_id: string; action_type: string; is_simulated?: boolean; payload?: any; reason?: string }) =>
    fetchJson<CaseAction>(`${BASE_URL}/api/actions/propose`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  executeAction: (actionId: string, simulatedOutcome?: string) =>
    fetchJson<CaseAction>(`${BASE_URL}/api/actions/${actionId}/execute`, {
      method: 'POST',
      body: JSON.stringify({ simulated_outcome: simulatedOutcome }),
    }),

  verifyAction: (actionId: string) =>
    fetchJson<CaseAction>(`${BASE_URL}/api/actions/${actionId}/verify`, {
      method: 'POST',
      body: JSON.stringify({}),
    }),

  // Approvals
  getApprovals: () => fetchJson<ApprovalRecord[]>(`${BASE_URL}/api/approvals`),

  approveAction: (actionId: string, reason?: string) =>
    fetchJson<CaseAction>(`${BASE_URL}/api/actions/${actionId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ decision: 'APPROVE', reason, reviewer: 'HUMAN_OPERATOR' }),
    }),

  rejectAction: (actionId: string, reason?: string) =>
    fetchJson<CaseAction>(`${BASE_URL}/api/actions/${actionId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ decision: 'REJECT', reason, reviewer: 'HUMAN_OPERATOR' }),
    }),

  // AI Agent Chat
  sendAgentMessage: (message: string, caseId?: string) =>
    fetchJson<AgentChatResponse>(`${BASE_URL}/api/agent/chat`, {
      method: 'POST',
      body: JSON.stringify({ message, case_id: caseId }),
    }),

  // Audit
  getAuditEvents: (caseId?: string, limit: number = 50) => {
    const q = new URLSearchParams({ limit: String(limit) });
    if (caseId) q.append('case_id', caseId);
    return fetchJson<AuditEvent[]>(`${BASE_URL}/api/audit?${q.toString()}`);
  },

  // Integrations & CSV Import
  getIntegrations: () => fetchJson<IntegrationConnection[]>(`${BASE_URL}/api/integrations`),

  importCsv: async (file: File, recordType: string): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('record_type', recordType);

    const resp = await fetch(`${BASE_URL}/api/import/csv`, {
      method: 'POST',
      body: formData,
    });

    if (!resp.ok) {
      let errText = 'CSV import failed';
      try {
        const errJson = await resp.json();
        if (errJson.detail) errText = errJson.detail;
      } catch (_) {}
      throw new Error(errText);
    }
    return resp.json();
  },

  // Demo Reset
  resetDemoData: () =>
    fetchJson<{ status: string; message: string }>(`${BASE_URL}/api/demo/reset`, {
      method: 'POST',
    }),

  // Business Database & Software Ingestion
  uploadBusinessDatabase: async (file: File, wipeDemo: boolean = false): Promise<BusinessCrawlResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('wipe_demo', String(wipeDemo));

    const resp = await fetch(`${BASE_URL}/api/business/upload-database`, {
      method: 'POST',
      body: formData,
    });

    if (!resp.ok) {
      let errText = 'Failed to upload business database';
      try {
        const errJson = await resp.json();
        if (errJson.detail) errText = errJson.detail;
      } catch (_) {}
      throw new Error(errText);
    }
    return resp.json();
  },

  uploadBusinessJson: async (file: File, wipeDemo: boolean = false): Promise<BusinessCrawlResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('wipe_demo', String(wipeDemo));

    const resp = await fetch(`${BASE_URL}/api/business/upload-json`, {
      method: 'POST',
      body: formData,
    });

    if (!resp.ok) {
      let errText = 'Failed to upload business JSON';
      try {
        const errJson = await resp.json();
        if (errJson.detail) errText = errJson.detail;
      } catch (_) {}
      throw new Error(errText);
    }
    return resp.json();
  },

  connectBusinessSoftware: async (params: {
    provider: string;
    apiKey?: string;
    environment?: string;
    accountId?: string;
  }): Promise<{ status: string; provider: string; connection_status: string; message: string }> => {
    const formData = new FormData();
    formData.append('provider', params.provider);
    if (params.apiKey) formData.append('api_key', params.apiKey);
    if (params.environment) formData.append('environment', params.environment);
    if (params.accountId) formData.append('account_id', params.accountId);

    const resp = await fetch(`${BASE_URL}/api/business/connect-software`, {
      method: 'POST',
      body: formData,
    });

    if (!resp.ok) {
      let errText = 'Failed to connect software';
      try {
        const errJson = await resp.json();
        if (errJson.detail) errText = errJson.detail;
      } catch (_) {}
      throw new Error(errText);
    }
    return resp.json();
  },

  clearBusinessData: () =>
    fetchJson<{ status: string; message: string }>(`${BASE_URL}/api/business/clear-demo-data`, {
      method: 'POST',
    }),

  getBusinessAuditSummary: () =>
    fetchJson<BusinessAuditSummary>(`${BASE_URL}/api/business/audit-summary`),

  // Local Session & Device Storage
  recordSessionEvent: (eventType: string, data?: any, sessionId?: string) =>
    fetchJson<{ status: string; event: any }>(`${BASE_URL}/api/session/event`, {
      method: 'POST',
      body: JSON.stringify({
        event_type: eventType,
        actor: 'USER',
        data,
        session_id: sessionId || 'browser_local_session',
      }),
    }),

  getSessionEvents: (limit: number = 200) =>
    fetchJson<{ status: string; total_events: number; events: any[] }>(
      `${BASE_URL}/api/session/events?limit=${limit}`
    ),

  clearSessionEvents: () =>
    fetchJson<{ status: string; message: string }>(`${BASE_URL}/api/session/events`, {
      method: 'DELETE',
    }),

  // Sample Enterprise Vulnerabilities Dataset
  getSampleVulnerabilitiesInfo: () =>
    fetchJson<{
      organization: string;
      description: string;
      total_revenue_at_risk: string;
      vulnerabilities: Array<{
        category: string;
        severity: string;
        vulnerability: string;
        affected_customer: string;
        recommended_action: string;
      }>;
      db_filename: string;
      json_filename: string;
    }>(`${BASE_URL}/api/business/sample-vulnerabilities-info`),

  loadVulnerabilitiesDataset: async (wipeDemo: boolean = true): Promise<BusinessCrawlResult> => {
    const formData = new FormData();
    formData.append('wipe_demo', String(wipeDemo));
    const resp = await fetch(`${BASE_URL}/api/business/load-vulnerabilities-dataset`, {
      method: 'POST',
      body: formData,
    });
    if (!resp.ok) {
      let errText = 'Failed to load enterprise vulnerability dataset';
      try {
        const errJson = await resp.json();
        if (errJson.detail) errText = errJson.detail;
      } catch (_) {}
      throw new Error(errText);
    }
    return resp.json();
  },

  getDownloadVulnerabilitiesUrl: (format: 'db' | 'json') =>
    `${BASE_URL}/api/business/download-vulnerabilities-file?format=${format}`,
};
