import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  History,
  RotateCw,
  ExternalLink,
} from 'lucide-react';
import { ApprovalRecord } from '../types';
import { api } from '../api/client';

interface ApprovalsPageProps {
  onSelectCaseId: (caseId: string) => void;
  onRefreshSummary: () => void;
}

export const ApprovalsPage: React.FC<ApprovalsPageProps> = ({
  onSelectCaseId,
  onRefreshSummary,
}) => {
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchApprovals = async () => {
    setLoading(true);
    try {
      const data = await api.getApprovals();
      setApprovals(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleDecision = async (actionId: string, decision: 'APPROVE' | 'REJECT') => {
    setProcessingId(actionId);
    setActionError(null);
    try {
      if (decision === 'APPROVE') {
        await api.approveAction(actionId, 'Approved by human reviewer from Approval Center');
      } else {
        await api.rejectAction(actionId, 'Rejected by human reviewer from Approval Center');
      }
      await fetchApprovals();
      onRefreshSummary();
    } catch (err: any) {
      setActionError(err.message || 'Operation failed');
    } finally {
      setProcessingId(null);
    }
  };

  const pendingList = approvals.filter((a) => a.status === 'PENDING');
  const historyList = approvals.filter((a) => a.status !== 'PENDING');

  return (
    <div className="space-y-6">
      {/* Top Banner Notice */}
      <div className="p-4 rounded-xl glass-card border-amber-500/30 flex items-center justify-between gap-4 bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-950">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-amber-600/20 text-amber-400 border border-amber-500/30">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Human-in-the-Loop Approval Queue</h2>
            <p className="text-xs text-slate-400">
              High-value transactions (≥ $500.00), multiple payment retries, and customer demand
              notices require explicit human review before execution.
            </p>
          </div>
        </div>
        <button
          onClick={fetchApprovals}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
          title="Refresh approvals"
        >
          <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
        </button>
      </div>

      {actionError && (
        <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 text-xs rounded-lg">
          {actionError}
        </div>
      )}

      {/* Pending Approvals Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <span>Pending Review</span>
            <span className="px-2 py-0.5 rounded-full text-xs font-mono bg-amber-500 text-slate-950 font-bold">
              {pendingList.length}
            </span>
          </h3>
        </div>

        {pendingList.length === 0 ? (
          <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center text-xs text-slate-400">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
            <p className="font-semibold text-slate-200">No Pending Approvals</p>
            <p className="text-slate-500 mt-1">All proposed recovery actions have been reviewed.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pendingList.map((appr) => (
              <div
                key={appr.id}
                className="glass-card p-5 rounded-2xl border-amber-500/30 ring-1 ring-amber-500/20 space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] font-mono uppercase bg-amber-950/80 text-amber-300 border border-amber-800/80 px-2 py-0.5 rounded">
                        Requires Oversight
                      </span>
                      <h4 className="text-base font-bold text-white font-mono mt-1.5 flex items-center gap-2">
                        <span>{appr.case_id}</span>
                        <button
                          onClick={() => onSelectCaseId(appr.case_id)}
                          className="text-slate-400 hover:text-white"
                          title="View case details"
                        >
                          <ExternalLink className="w-4 h-4 text-indigo-400" />
                        </button>
                      </h4>
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                      {new Date(appr.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>

                  {/* Proposed Action */}
                  <div className="p-3 bg-slate-900/90 rounded-xl border border-slate-800 text-xs space-y-1">
                    <span className="text-slate-500 block">Proposed Action:</span>
                    <span className="font-mono font-bold text-indigo-300 text-sm">
                      {appr.action?.action_type || 'SIMULATED_PAYMENT_RETRY'}
                    </span>
                  </div>

                  {/* Rationale & Consequence Warning */}
                  <div className="space-y-1.5 text-xs">
                    <div>
                      <span className="text-slate-400 font-medium">Business Reason:</span>
                      <p className="text-slate-200">{appr.reason || 'Trigger recovery retry'}</p>
                    </div>
                    <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-900/60 text-amber-200 text-xs flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold block">Potential Consequence:</span>
                        <span>{appr.potential_consequence || 'Direct customer charge retry'}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Approve / Reject Controls */}
                <div className="flex items-center gap-3 pt-3 border-t border-slate-800/80">
                  <button
                    onClick={() => handleDecision(appr.action_id, 'REJECT')}
                    disabled={processingId === appr.action_id}
                    className="flex-1 py-2 rounded-xl text-xs font-semibold bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800/60 flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </button>

                  <button
                    onClick={() => handleDecision(appr.action_id, 'APPROVE')}
                    disabled={processingId === appr.action_id}
                    className="flex-1 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 flex items-center justify-center gap-1.5 transition-all disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Authorize</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Historical Approvals Table */}
      <div className="space-y-3 pt-4">
        <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <History className="w-4 h-4 text-slate-400" />
          <span>Past Approval Decisions</span>
        </h3>

        <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="py-3 px-4">Case ID</th>
                  <th className="py-3 px-4">Action Type</th>
                  <th className="py-3 px-4">Decision</th>
                  <th className="py-3 px-4">Reviewer</th>
                  <th className="py-3 px-4">Reviewed At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {historyList.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-slate-500">
                      No historical approval decisions recorded yet.
                    </td>
                  </tr>
                ) : (
                  historyList.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 font-mono font-bold text-indigo-300">
                        {item.case_id}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {item.action?.action_type || 'RECOVERY_ACTION'}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.status === 'APPROVED'
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                              : 'bg-rose-950 text-rose-300 border border-rose-800'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{item.reviewer}</td>
                      <td className="py-3 px-4 text-slate-400 font-mono">
                        {item.reviewed_at ? new Date(item.reviewed_at).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
