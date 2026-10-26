import React, { useState } from 'react';
import {
  X,
  CreditCard,
  FileText,
  ShoppingCart,
  User,
  ShieldAlert,
  Play,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  History,
  Send,
} from 'lucide-react';
import { RecoveryCase } from '../types';
import { PriorityBadge } from './PriorityBadge';
import { StatusBadge } from './StatusBadge';
import { api } from '../api/client';

interface CaseDrawerProps {
  caseData: RecoveryCase | null;
  isOpen: boolean;
  onClose: () => void;
  onCaseUpdated: () => void;
}

export const CaseDrawer: React.FC<CaseDrawerProps> = ({
  caseData,
  isOpen,
  onClose,
  onCaseUpdated,
}) => {
  const [loading, setLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  if (!isOpen || !caseData) return null;

  const priorityReasons: string[] = (() => {
    try {
      return JSON.parse(caseData.priority_reasons || '[]');
    } catch {
      return [];
    }
  })();

  const activeAction = caseData.actions.find((a) =>
    ['PROPOSED', 'PENDING_APPROVAL', 'APPROVED', 'EXECUTING', 'EXECUTED'].includes(a.status)
  );

  const handleProposeAction = async () => {
    setLoading(true);
    setActionError(null);
    try {
      await api.proposeAction({
        case_id: caseData.id,
        action_type: caseData.recommended_action || 'SIMULATED_PAYMENT_RETRY',
        is_simulated: true,
        reason: 'Operator proposed recommended recovery action via case inspection drawer',
      });
      onCaseUpdated();
    } catch (err: any) {
      setActionError(err.message || 'Failed to propose action');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (actionId: string) => {
    setLoading(true);
    setActionError(null);
    try {
      await api.approveAction(actionId, 'Approved by human reviewer from case drawer');
      onCaseUpdated();
    } catch (err: any) {
      setActionError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (actionId: string) => {
    setLoading(true);
    setActionError(null);
    try {
      await api.rejectAction(actionId, 'Rejected by human reviewer from case drawer');
      onCaseUpdated();
    } catch (err: any) {
      setActionError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (actionId: string) => {
    setLoading(true);
    setActionError(null);
    try {
      await api.executeAction(actionId, 'SUCCESS');
      onCaseUpdated();
    } catch (err: any) {
      setActionError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (actionId: string) => {
    setLoading(true);
    setActionError(null);
    try {
      await api.verifyAction(actionId);
      onCaseUpdated();
    } catch (err: any) {
      setActionError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/70 backdrop-blur-sm flex justify-end animate-in fade-in duration-150">
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full overflow-hidden text-slate-100">
        {/* Drawer Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-900/90">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-indigo-400 font-bold">{caseData.id}</span>
              <span className="text-xs uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold border border-slate-700">
                {caseData.source_type.replace('_', ' ')}
              </span>
            </div>
            <div className="text-2xl font-bold font-mono text-white mt-2">
              ${(caseData.amount_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              <span className="text-sm font-sans font-normal text-slate-400 ml-2">
                {caseData.currency}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Status & Priority Row */}
          <div className="flex flex-wrap items-center gap-3 p-4 rounded-xl bg-slate-950/50 border border-slate-800/80">
            <div>
              <span className="text-[11px] uppercase tracking-wider text-slate-400 block mb-1">
                Lifecycle Status
              </span>
              <StatusBadge status={caseData.status} />
            </div>
            <div className="h-8 w-px bg-slate-800 mx-2 hidden sm:block" />
            <div>
              <span className="text-[11px] uppercase tracking-wider text-slate-400 block mb-1">
                Priority Ranking
              </span>
              <PriorityBadge
                priority={caseData.priority}
                score={caseData.priority_score}
                showScore={true}
              />
            </div>
          </div>

          {/* Customer Profile */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <User className="w-4 h-4 text-slate-400" />
              Customer Information
            </h4>
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 text-sm space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-400">Account Name:</span>
                <span className="font-medium text-white">{caseData.customer?.name || 'Unknown'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Email:</span>
                <span className="font-mono text-slate-200">{caseData.customer?.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Reference:</span>
                <span className="font-mono text-slate-400">{caseData.customer?.customer_ref}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Source External ID:</span>
                <span className="font-mono text-slate-300">{caseData.source_id}</span>
              </div>
            </div>
          </div>

          {/* Failure Diagnostics & Recovery Guardrail */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              Diagnostics & Guardrails
            </h4>
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 text-sm space-y-2">
              <div>
                <span className="text-xs text-slate-400 block">Failure Reason / Drop-off Note:</span>
                <p className="text-slate-200 mt-0.5 font-medium">{caseData.failure_reason}</p>
              </div>

              {caseData.source_type === 'abandoned_checkout' && (
                <div className="p-3 bg-amber-950/50 border border-amber-800/80 rounded-lg text-xs text-amber-200 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <span>
                    <strong>Safety Guardrail Active:</strong> Abandoned checkouts cannot be charged
                    directly. Automated recovery is restricted to customer recovery reminders or discount
                    incentives.
                  </span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                <div>
                  <span className="text-slate-400">Retries Used:</span>{' '}
                  <span className="font-mono font-medium text-slate-200">
                    {caseData.retry_count} / {caseData.max_retries}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Cooldown State:</span>{' '}
                  <span className="font-medium text-slate-200">
                    {caseData.cooldown_until ? 'Active 24h Cooldown' : 'Clear / Ready'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Transparent Multi-Factor Priority Breakdown */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-400" />
              Priority Score Formula ({caseData.priority_score}/100)
            </h4>
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 space-y-2">
              <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    caseData.priority_score >= 80
                      ? 'bg-rose-500'
                      : caseData.priority_score >= 60
                      ? 'bg-amber-500'
                      : 'bg-indigo-500'
                  }`}
                  style={{ width: `${caseData.priority_score}%` }}
                />
              </div>
              <ul className="text-xs text-slate-300 space-y-1.5 pt-2">
                {priorityReasons.map((reason, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-indigo-400 font-bold">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Recovery Actions History */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <History className="w-4 h-4 text-slate-400" />
              Recovery Actions & Verification Receipts
            </h4>
            {caseData.actions.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800/80 text-xs text-slate-500 text-center">
                No recovery actions recorded yet.
              </div>
            ) : (
              <div className="space-y-2.5">
                {caseData.actions.map((act) => (
                  <div
                    key={act.id}
                    className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-indigo-300 font-semibold">{act.action_type}</span>
                      <StatusBadge status={act.status} isSimulated={act.is_simulated} />
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Idempotency Key:</span>
                      <span className="font-mono text-[11px] text-slate-300">{act.idempotency_key}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Verification Status:</span>
                      <span
                        className={`font-semibold ${
                          act.verification_status === 'VERIFIED_CONFIRMED'
                            ? 'text-emerald-400'
                            : act.verification_status === 'VERIFIED_FAILED'
                            ? 'text-rose-400'
                            : 'text-amber-400'
                        }`}
                      >
                        {act.verification_status}
                      </span>
                    </div>
                    {act.error_message && (
                      <p className="text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900/50 mt-1">
                        {act.error_message}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {actionError && (
            <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 text-xs rounded-lg">
              {actionError}
            </div>
          )}
        </div>

        {/* Drawer Action Controls Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex flex-col gap-2">
          {caseData.is_resolved ? (
            <div className="p-3 bg-emerald-950/50 border border-emerald-800/60 rounded-xl text-center text-xs text-emerald-300 font-medium">
              Case resolved ({caseData.resolution_outcome}). No further recovery actions required.
            </div>
          ) : activeAction ? (
            <div className="space-y-2">
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Active Action in Progress:</span>
                <span className="font-mono text-indigo-300 font-semibold">
                  {activeAction.action_type}
                </span>
              </div>

              {activeAction.status === 'PENDING_APPROVAL' && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleApprove(activeAction.id)}
                    disabled={loading}
                    className="flex-1 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Approve Action</span>
                  </button>
                  <button
                    onClick={() => handleReject(activeAction.id)}
                    disabled={loading}
                    className="flex-1 py-2 rounded-xl text-xs font-semibold bg-rose-900 hover:bg-rose-800 text-rose-200 flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <X className="w-4 h-4" />
                    <span>Reject</span>
                  </button>
                </div>
              )}

              {activeAction.status === 'APPROVED' && (
                <button
                  onClick={() => handleExecute(activeAction.id)}
                  disabled={loading}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition-all"
                >
                  <Play className="w-4 h-4" />
                  <span>Execute Simulated Action ({activeAction.action_type})</span>
                </button>
              )}

              {activeAction.status === 'EXECUTED' && (
                <button
                  onClick={() => handleVerify(activeAction.id)}
                  disabled={loading}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/30 transition-all"
                >
                  <RotateCw className="w-4 h-4" />
                  <span>Verify Recovery Outcome</span>
                </button>
              )}
            </div>
          ) : (
            <button
              onClick={handleProposeAction}
              disabled={loading}
              className="w-full py-2.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all"
            >
              <Send className="w-4 h-4" />
              <span>Propose Recommended Action ({caseData.recommended_action})</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
