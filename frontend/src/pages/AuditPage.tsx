import React, { useState, useEffect } from 'react';
import { FileText, Filter, RefreshCw, Search, Shield, ChevronDown, ChevronUp } from 'lucide-react';
import { AuditEvent } from '../types';
import { api } from '../api/client';

interface AuditPageProps {
  onSelectCaseId: (caseId: string) => void;
}

export const AuditPage: React.FC<AuditPageProps> = ({ onSelectCaseId }) => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [caseFilter, setCaseFilter] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchAudit = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditEvents(caseFilter || undefined, 100);
      setEvents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudit();
  }, [caseFilter]);

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-indigo-400" />
            <span>Immutable Recovery Audit Trail</span>
          </h2>
          <p className="text-xs text-slate-400">
            Records all system detections, agent recommendations, approvals, simulated executions, and
            gateway receipts.
          </p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter by case ID..."
              value={caseFilter}
              onChange={(e) => setCaseFilter(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            onClick={fetchAudit}
            className="p-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-300 hover:text-white"
            title="Refresh log"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
              <tr>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Case Reference</th>
                <th className="py-3 px-4">Audit Description</th>
                <th className="py-3 px-4 text-center">Designation</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {loading && events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    Loading audit events...
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    No audit records found.
                  </td>
                </tr>
              ) : (
                events.map((evt) => {
                  const isExpanded = expandedId === evt.id;
                  return (
                    <React.Fragment key={evt.id}>
                      <tr className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                          {new Date(evt.created_at).toISOString().replace('T', ' ').substring(0, 19)}
                        </td>

                        <td className="py-3 px-4 font-mono font-bold text-indigo-300">
                          {evt.event_type}
                        </td>

                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                            {evt.actor}
                          </span>
                        </td>

                        <td className="py-3 px-4 font-mono font-bold">
                          {evt.case_id ? (
                            <button
                              onClick={() => onSelectCaseId(evt.case_id!)}
                              className="text-indigo-400 hover:underline"
                            >
                              {evt.case_id}
                            </button>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>

                        <td className="py-3 px-4 text-slate-200 max-w-md">{evt.description}</td>

                        <td className="py-3 px-4 text-center">
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                              evt.is_simulated
                                ? 'bg-purple-950/60 text-purple-300 border-purple-800/60'
                                : 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                            }`}
                          >
                            {evt.is_simulated ? 'SIMULATED' : 'LIVE'}
                          </span>
                        </td>

                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setExpandedId(isExpanded ? null : evt.id)}
                            className="p-1 rounded text-slate-400 hover:text-white"
                          >
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )}
                          </button>
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr className="bg-slate-950/90">
                          <td colSpan={7} className="p-4 border-b border-slate-800">
                            <div className="text-[11px] font-mono space-y-1">
                              <span className="text-slate-500 font-bold block">
                                Metadata Payload:
                              </span>
                              <pre className="text-emerald-400 bg-slate-900 p-3 rounded-lg border border-slate-800 overflow-x-auto">
                                {JSON.stringify(JSON.parse(evt.metadata_json || '{}'), null, 2)}
                              </pre>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
